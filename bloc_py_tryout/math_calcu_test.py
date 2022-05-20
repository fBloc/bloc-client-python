import unittest

from bloc_client import *

from bloc_py_tryout.math_calcu import MathCalcu


class TestMathCalcuNode(unittest.TestCase):
    def setUp(self):
        self.client = BlocClient.new_client("")

    def test_add(self):
        opt = self.client.test_run_function(
            MathCalcu(),
            [
                [  # ipt 0
                    [1, 2]  # component 0, numbers
                ],
                [  # ipt 1
                    1  # "+" operater
                ],
            ]
        )
        assert isinstance(opt, FunctionRunOpt), "opt should be FunctionRunOpt type"
        self.assertIsInstance(opt, FunctionRunOpt, "opt is not FunctionRunOpt type")
        self.assertTrue(opt.suc, "should suc")
        self.assertFalse(opt.intercept_below_function_run, "should not intercept below function run")
        self.assertEqual(opt.optKey_map_data['result'], 3, "result should be 3")


if __name__ == '__main__':
    unittest.main()
