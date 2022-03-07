import docker
from rigelcore.exceptions import (
    DockerAPIError,
    DockerOperationError,
    InvalidDockerClientInstanceError,
    InvalidDockerImageNameError,
)
from rigelcore.loggers import DockerLogPrinter
from typing import Dict, Optional


class DockerClient:
    """
    A wrapper class for the docker.client.DockerClient.
    Keeps the same functionality but allows for error handling that suits better Rigel.
    """

    # A Docker client instance.
    client: docker.client.DockerClient

    def __init__(self, client: Optional[docker.client.DockerClient] = None) -> None:
        """
        Create a Docker client instance.

        :type client: Optioanl[docker.client.DockerClient]
        :param client: A Docker client instance.
        """
        if client:
            if not isinstance(client, docker.client.DockerClient):
                raise InvalidDockerClientInstanceError()
            self.client = client
        else:
            try:
                self.client = docker.from_env()
            except docker.errors.DockerException as exception:
                raise DockerAPIError(exception=exception)

    def print_logs(self, image: docker.models.images.Image) -> None:
        """
        Display Docker log messages for a given Docker image.

        :type image: docker.models.images.Image
        :param image: The Docker image.
        """
        printer = DockerLogPrinter()

        iterator = iter(image)
        while True:
            try:
                log = next(iterator)
                printer.log(log)
            except StopIteration:  # no more log messages
                if 'error' in log:
                    raise DockerOperationError(msg=log['error'])
                break

    def build(self, path: str, dockerfile: str, image: str, buildargs: Dict[str, str]) -> None:
        """
        Build a new Docker image.

        :type path: string
        :param path: Root of the build context.
        :type dockerfile: string
        :param dockerfile: Path for the Dockerfile.
        :type image: string
        :param image: The name for the new Docker image.
        :type buildargs: Dict[str, str]
        :param buildargs: Build arguments.
        """
        try:
            built_image = self.client.api.build(
                path=path,
                dockerfile=dockerfile,
                tag=image,
                buildargs=buildargs,
                decode=True,
                rm=True
            )
            self.print_logs(built_image)
        except docker.errors.DockerException as exception:
            raise DockerAPIError(exception=exception)

    def tag(self, source_image: str, target_image: str) -> None:
        """
        Create a Docker image that references an existing Docker image.

        :type source_image: string
        :param source_image: The name of the image being referenced.
        :type target_image: string
        :param target_image: The desired name for the new image.
        """
        if ':' in target_image:
            try:
                desired_image_name, desired_image_tag = target_image.split(':')
            except ValueError:
                raise InvalidDockerImageNameError(image=target_image)
        else:
            desired_image_name = target_image
            desired_image_tag = 'latest'

        try:
            self.client.api.tag(
                image=source_image,
                repository=desired_image_name,
                tag=desired_image_tag
            )
        except docker.errors.DockerException as exception:
            raise DockerAPIError(exception=exception)

    def login(self, registry: str, username: str, password: str) -> None:
        """
        Authenticate user with a given Docker image regisry.

        :type registry: string
        :param registry: The registry to authenticate with.
        :type username: string
        :param username: The registry username.
        :type password: string
        :param password: The registry password.
        """
        try:
            self.client.api.login(
                username=username,
                password=password,
                registry=registry
            )
        except docker.errors.DockerException as exception:
            raise DockerAPIError(exception=exception)

    def push(self, image: str) -> None:
        """
        Push a Docker image to a Docker image registry.

        :type image: string
        :param image: The name of the Docker image.
        """
        try:
            pushed_image = self.client.api.push(image, stream=True, decode=True)
            self.print_logs(pushed_image)
        except docker.errors.DockerException as exception:
            raise DockerAPIError(exception=exception)

    def network_exists(self, name: str) -> bool:
        """
        Verify if a Docker network already exists.

        :type name: string
        :param name: The name of the Docker network.

        :rtype: bool
        :return: True if a Docker network already exists
        with the provided name. False otherwise.
        """
        try:
            return bool(self.client.networks.list(names=[name]))
        except docker.errors.DockerException as exception:
            raise DockerAPIError(exception=exception)

    def create_network(self, name: str, driver: str) -> None:
        """
        Create a Docker network.

        :type name: string
        :param name: The name of the Docker network.
        :type driver: string
        :param driver: Name of driver used to create the network.
        """
        if not self.network_exists(name):
            try:
                self.client.networks.create(
                    name,
                    driver=driver
                )
            except docker.errors.DockerException as exception:
                raise DockerAPIError(exception=exception)
