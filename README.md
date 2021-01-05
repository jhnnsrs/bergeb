# Bergen

### Idea

Bergen is the API-Client for the Arnheim Framework

 
### Prerequisites

Bergen only works with a running Arnheim Instance (in your network or locally for debugging).

### Usage

In order to initialize the Client you need to connect it as a Valid Application with your Arnheim Instance

```python
client = Bergen(host="p-tnagerl-lab1",
    port=8000,
  client_id="APPLICATION_ID_FROM_ARNHEIM", 
  client_secret="APPLICATION_SECRET_FROM_ARNHEIM",
  name="karl",
)
```

In your following code you can simple query your data according to the Schema of the Datapoint

```python
from bergen.schema import Node

node = Node.objects.get(id=1)
print(node.name)

```

## Access Data from different Datapoints

The Arnheim Framework is able to provide data from different Data Endpoints through a commong GraphQL Interface
. This allows you to access data from various different storage formats like Elements and Omero and interact without
knowledge of their underlying api.

Each Datapoint provides a typesafe schema. Arnheim Elements provides you with an implemtation of that schema.

## Provide a Template for a Node

Documentation neccesary


### Testing and Documentation

So far Bergen does only provide limitedunit-tests and is in desperate need of documentation,
please beware that you are using an Alpha-Version


### Build with

- [Arnheim](https://github.com/jhnnsrs/arnheim)
- [Pydantic](https://github.com/jhnnsrs/arnheim)


#### Features

- Scss
- [Domain-style](https://github.com/reactjs/redux/blob/master/docs/faq/CodeStructure.md) for code structure
- Bundle Size analysis
- Code splitting with [react-loadable](https://github.com/jamiebuilds/react-loadable)


## Roadmap

This is considered pre-Alpha so pretty much everything is still on the roadmap


## Deployment

Contact the Developer before you plan to deploy this App, it is NOT ready for public release

## Versioning

There is not yet a working versioning profile in place, consider non-stable for every release 

## Authors

* **Johannes Roos ** - *Initial work* - [jhnnsrs](https://github.com/jhnnsrs)

See also the list of [contributors](https://github.com/your/project/contributors) who participated in this project.

## License

Attribution-NonCommercial 3.0 Unported (CC BY-NC 3.0) 

## Acknowledgments

* EVERY single open-source project this library used (the list is too extensive so far)