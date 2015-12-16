"""Various helper utilities to calculate reversible one-to-one mappings of sensitive ids"""

import base64
import numpy as np
import random
import luigi


def encode_id(scope, id_type, id_value):
    """Encode a scope-type-value tuple into a single ID string."""
    return base64.b32encode('|'.join([scope, id_type, id_value]))


def decode_id(encoded_id):
    """Decode an ID string back to the original scope-type-value tuple."""
    scope, id_type, id_value = base64.b32decode(encoded_id).split('|')
    return scope, id_type, id_value


class PermutationGenerator(object):
    """Class to calculate reversible 1-1 mapping using a permutation matrix."""

    def __init__(self, seed, matrix_dim, bits):
        self.bits = bits
        self.permutation_matrix = self.random_permutation_matrix(seed, matrix_dim)

    def int_to_binvec(self, int_value):
        """Convert int_value, which must be less than 2**bits, to an np vector of bits 0/1 bits."""
        if int_value < 0 or int_value >= 2 ** self.bits:
            raise ValueError("{} out of range [0, 2**{}]".format(int_value, self.bits))

        str_int_value = bin(int_value)[2:].zfill(self.bits)
        return np.array([int(b) for b in str_int_value])

    def binvec_to_int(self, vec):
        """Convert an np array of bits (type int) to a real int."""
        # more string hacks
        return int("".join(map(str, vec)), 2)

    def random_permutation_matrix(self, seed, matrix_dim):
        """Return a random permutation matrix of dimension matrix_dim using seed."""
        rng = random.Random(seed)
        # where does each bit go?
        mapping = range(matrix_dim)
        rng.shuffle(mapping)
        # Now make a matrix that does that
        permutation = np.zeros((matrix_dim, matrix_dim), dtype=int)
        for i in range(matrix_dim):
            permutation[i, mapping[i]] = 1
        return permutation

    def permute(self, int_value):
        """Given int int_value with bits bits, permute it using the specified bits-by-bits permutation."""
        vec = self.int_to_binvec(int_value)
        permuted = vec.dot(self.permutation_matrix)
        return self.binvec_to_int(permuted)

    def unpermute(self, int_value):
        """Given int int_value with bits bits, unpermute it using the specified bits-by-bits permutation."""
        vec = self.int_to_binvec(int_value)
        permuted = vec.dot(self.permutation_matrix.T)
        return self.binvec_to_int(permuted)


class UserIdRemapperMixin(object):
    """Mixin class to provide rempad_id method. Ensures that there is only one instace of PermutationGenerator."""

    seed_value = luigi.IntParameter(
        config_path={'section': 'id-codec', 'name': 'seed_value'}
    )
    __generator_instance = None

    def __init__(self, *args, **kwargs):
        super(UserIdRemapperMixin, self).__init__(*args, **kwargs)
        if UserIdRemapperMixin.__generator_instance is None:
            UserIdRemapperMixin.__generator_instance = PermutationGenerator(self.seed_value, 32, 32)
        self.permutation_generator = UserIdRemapperMixin.__generator_instance

    def remap_id(self, id_value):
        "Returns a reversible mapping of input id."
        return self.permutation_generator.permute(int(id_value))