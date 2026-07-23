import unittest

from ratelimit import RateLimiter


class RateLimiterTest(unittest.TestCase):
    def test_allows_up_to_the_limit(self):
        limiter = RateLimiter(max_requests=3, window_seconds=3600)
        self.assertTrue(limiter.allow('1.2.3.4'))
        self.assertTrue(limiter.allow('1.2.3.4'))
        self.assertTrue(limiter.allow('1.2.3.4'))

    def test_blocks_after_the_limit(self):
        limiter = RateLimiter(max_requests=2, window_seconds=3600)
        limiter.allow('1.2.3.4')
        limiter.allow('1.2.3.4')
        self.assertFalse(limiter.allow('1.2.3.4'))

    def test_tracks_keys_independently(self):
        limiter = RateLimiter(max_requests=1, window_seconds=3600)
        self.assertTrue(limiter.allow('1.2.3.4'))
        self.assertTrue(limiter.allow('5.6.7.8'))
        self.assertFalse(limiter.allow('1.2.3.4'))

    def test_old_hits_expire_out_of_the_window(self):
        clock = {'t': 0.0}
        limiter = RateLimiter(max_requests=1, window_seconds=60, clock=lambda: clock['t'])
        self.assertTrue(limiter.allow('1.2.3.4'))
        self.assertFalse(limiter.allow('1.2.3.4'))
        clock['t'] += 61
        self.assertTrue(limiter.allow('1.2.3.4'))


if __name__ == '__main__':
    unittest.main()
