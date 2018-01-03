import unittest
from pijp_dti import dti

class Test(unittest.TestCase):

    def test_Stage(self):

        stage = dti.Stage('test', '001', None)

        stage.working_dir = '/home/vhasfcellis/tests/'
        stage.logdir = '/home/vhasfcellisr/tests/'

        stage.run()


