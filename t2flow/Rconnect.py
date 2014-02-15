from balcaza.t2types import Integer
from balcaza.t2activity import RServer
from balcaza.t2flow import Workflow

flow = Workflow("Check that R is running on localhost")

rserve = RServer()

Test = flow.task.Test << rserve.code(
	'out <- 28364',
	outputs = dict(
		out = Integer
		)
	)

Test.extendUnusedPorts()
