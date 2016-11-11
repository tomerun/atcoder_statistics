# coding: utf-8

import unittest

if __name__ == '__main__':
	tests = unittest.defaultTestLoader.discover('test')
	unittest.TextTestRunner().run(tests)


