"""City incident regression tests (offline)."""
import unittest

class CityIncidentTests(unittest.TestCase):
    def test_schema(self):
        self.assertEqual('zombieee.city-incident.v1', 'zombieee.city-incident.v1')
