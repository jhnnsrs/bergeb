from bergen.clients.default import Bergen
from bergen.models import Node
import matplotlib.pyplot as plt
import time
with Bergen() as client:

    node = Node.objects.get(package="Flow Boy", interface="constantadder")

    with node.reserve() as res:
        result = res.assign(1)

        time.sleep(3)

        result = res.assign(2)
        print(result)
    


