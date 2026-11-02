import unittest
from App.cpu_gauge import gradient
from App.telemetry import Telemetry
class CPUTests(unittest.TestCase):
 def test_gradient(self):
  self.assertEqual(gradient(0).red(),25)
  self.assertEqual(gradient(1).red(),252)
 def test_sampling_interval_bounds(self):
  from PySide6.QtCore import QCoreApplication
  app=QCoreApplication.instance() or QCoreApplication([])
  service=Telemetry(50)
  self.assertEqual(service.timer.interval(),500)
  service.set_interval(100000)
  self.assertEqual(service.timer.interval(),60000)
