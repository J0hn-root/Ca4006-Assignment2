Instructions to run the project

1. Run docker image
docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3.11-management

- user:       guest
- password:   guest

2. Install python dependencies

- python -m pip install pika --upgrade