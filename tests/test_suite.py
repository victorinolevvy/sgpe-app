import unittest
from tests.test_basics import BasicsTestCase
from tests.test_user_model import UserModelTestCase
from tests.test_project_model import ProjectModelTestCase
from tests.test_main_routes import MainRoutesTestCase

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(BasicsTestCase))
    suite.addTest(unittest.makeSuite(UserModelTestCase))
    suite.addTest(unittest.makeSuite(ProjectModelTestCase))
    suite.addTest(unittest.makeSuite(MainRoutesTestCase))
    return suite

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
