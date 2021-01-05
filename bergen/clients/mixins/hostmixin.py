import inspect
from bergen.utils import ExpansionError, expandInputs
from aiostream.aiter_utils import async_
from bergen.constants import HOST_GQL, QUEUE_GQL
from bergen.helpers.pod import PodHelper
from bergen.helpers.host import HostHelper
from bergen.schema import Assignation, Node
import logging
import asyncio
from aiostream import stream, pipe
logger = logging.getLogger(__name__)

class HostMixIn:


    def __init__(self, name="test") -> None:
        self.name = name
        self.hostHelper = HostHelper(self) #

        super().__init__()


    def template(self, node: Node, version="standard", threaded=False):
        """Template is a decorator for marking a function as a Template

        Args:
            node (Node): The Node that you want to template for
            version (str, optional): Do you want to specify the version. Defaults to "standard".
            threaded (bool, optional): Should we run a pod of this template in a seperate thread?. Defaults to False.

        Returns:
            void
        """

        logger.info(f"Registering Node for {node.name}")
        volunteer = self.hostHelper.volunteer(node, version=version)

        def real_decorator(function):

            async def wrapper(assignation: Assignation):
                helper = PodHelper(volunteer, assignation, self)
                logger.info(f"Called with inputs {assignation.inputs}")

                try:
                    kwargs = expandInputs(node, assignation.inputs)
                except ExpansionError as e:
                    logger.error(e)
                    helper.critical(str(e))
                    return
                
                try:


                    if inspect.isasyncgenfunction(function):
                        # Exicting this is a generator who will yield results
                        yieldedresult = None
                        async for result in function(helper, **kwargs):
                            logger.info(f"Yielding {result}")
                            helper.nudge(result)
                            yieldedresult = result
                        
                        helper.end(yieldedresult)

                        return

                    if inspect.iscoroutinefunction(function):
                        result = await function(helper, **kwargs)
                        helper.end(result)

                        return


                    elif threaded:
                        # Threaded functions
                        threadhelper = None 
                        try: 
                            threadhelper = asyncio.to_thread
                        except:
                            logger.warn("Threading does not work below Python 3.9")
                        
                        if threadhelper:
                            result = await threadhelper(function, helper, **kwargs)
                        else:
                            result = function(helper, **kwargs)
                            helper.end(result)

                        return
                    else:
                        # We are dealing with a normal function. boring
                        result = function(helper, **assignation.inputs)
                        helper.end(result)

                        return
                    
                except Exception as e:
                    logger.error(e)
                    helper.critical(str(e))

                
                return 


            wrapper.__name__ = function.__name__
            self.hostHelper.addVolunteerFunction(volunteer, wrapper)

            return function


        return real_decorator


    async def host(self):

        volunteers = self.hostHelper.getVolunteers()

        queued = stream.merge(*[QUEUE_GQL.subscribe(ward=self.main_ward, variables= {"id": volunteer.id}) for volunteer in volunteers])
    
        assigned_pods = (queued 
            | pipe.action(lambda pod: self.hostHelper.addPod(pod)) # We are adding the Pod to the procedure
            | pipe.action(lambda pod: logger.warn(f"Got promoted to Host {pod}"))
        )
        
        assigned_assignations = (assigned_pods
             | pipe.flatmap(lambda pod: HOST_GQL.subscribe(ward=self.main_ward, variables={"pod": pod.id}))
             | pipe.action(lambda assignation: logger.warn(f"We are assigning this to our {assignation.inputs}"))
             | pipe.map(async_(lambda assignation: self.hostHelper.getFunctionForPod(assignation.pod)(assignation)))
             | pipe.map(lambda result: logger.info(f"Assignation finished with {result}"))
        )

        async with assigned_assignations.stream() as streamer:
            async for item in streamer:
                print(item)

        return True


    

    def run(self):
        logger.warn("Waiting for incoming Messages")

        loop = asyncio.get_event_loop()
        asyncio.run(self.host())



