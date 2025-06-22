import unittest
from tests.test_basics import BasicsTestCase

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(BasicsTestCase))
    return suite

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
