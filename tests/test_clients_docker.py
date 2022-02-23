import unittest
from rigelcore.clients import DockerClient
from rigelcore.exceptions import (
    DockerImageNotFoundError,
    DockerOperationError,
    InvalidDockerImageNameError,
    InvalidImageRegistryError
)
from unittest.mock import MagicMock, Mock, patch


class DockerClientTesting(unittest.TestCase):
    """
    Test suite for rigelcore.clients.DockerClient class.
    """

    @patch('rigelcore.clients.docker.DockerClient.print_logs')
    def test_client_image_build(self, print_mock: Mock) -> None:
        """
        Ensure that the creation of Docker images works as expected.
        """
        test_dockerfile_path = 'test_dockerfile_path'
        test_image = 'test_image'
        test_buildargs = {'TEST_VARIABLE': 'TEST_VALUE'}

        docker_mock_return_value = 'TestImageObject'
        docker_mock = MagicMock()
        docker_mock.build.return_value = docker_mock_return_value

        docker_client = DockerClient(docker_mock)
        docker_client.build(test_dockerfile_path, test_image, test_buildargs)

        docker_mock.build.assert_called_once_with(
            path='.',
            decode=True,
            rm=True,
            dockerfile=test_dockerfile_path,
            tag=test_image,
            buildargs=test_buildargs
        )
        print_mock.assert_called_once_with(docker_mock_return_value)

    def test_invalid_docker_image_name_error(self) -> None:
        """
        Ensure that InvalidDockerImageNameError is thrown if an invalid target image
        name is provided to function 'tag'.
        """
        test_target_image = 'invalid:image:name'
        with self.assertRaises(InvalidDockerImageNameError) as context:
            docker_client = DockerClient()
            docker_client.tag('test_source_image', test_target_image)
        self.assertEqual(context.exception.kwargs['image'], test_target_image)

    def test_docker_image_name_split_default_tag(self) -> None:
        """
        Ensure that the target Docker image name is properly split when
        it does not contain character ':'.
        """
        test_source_image = 'test_source_image'
        test_target_image = 'test_target_image'

        docker_mock = MagicMock()
        docker_client = DockerClient(docker_mock)
        docker_client.tag(test_source_image, test_target_image)

        docker_mock.tag.assert_called_once_with(
            image=test_source_image,
            repository=test_target_image,
            tag='latest'
        )

    def test_docker_image_name_split_semicolon(self) -> None:
        """
        Ensure that the target Docker image name is properly split when
        it contains character ':'.
        """
        test_source_image = 'test_source_image'
        test_target_image = 'test_target_image'
        test_target_tag = 'test_target_tag'
        complete_test_target_image = f'{test_target_image}:{test_target_tag}'

        docker_mock = MagicMock()
        docker_client = DockerClient(docker_mock)
        docker_client.tag(test_source_image, complete_test_target_image)

        docker_mock.tag.assert_called_once_with(
            image=test_source_image,
            repository=test_target_image,
            tag=test_target_tag
        )

    def test_docker_image_not_found_error(self) -> None:
        """
        Ensure that DockerImageNotFoundError is thrown if an invalid
        source image is referenced while using function 'tag'.
        """
        test_source_image = 'test_source_image'

        def raise_error(image: str, repository: str, tag: str) -> None:
            raise DockerImageNotFoundError(image=image)

        docker_mock = MagicMock()
        docker_mock.tag.side_effect = raise_error
        docker_mock.tag.return_value = None

        with self.assertRaises(DockerImageNotFoundError) as context:
            docker_client = DockerClient(docker_mock)
            docker_client.tag(test_source_image, 'test_target_image')
        self.assertEqual(context.exception.kwargs['image'], test_source_image)

    def test_invalid_image_registry_error(self) -> None:
        """
        Ensure that InvalidImageRegistryError is thrown if an invalid
        registry is referenced while using function 'login'.
        """
        test_registry = 'test_registry'

        def raise_error(username: str, password: str, registry: str) -> None:
            raise InvalidImageRegistryError(registry=registry)

        docker_mock = MagicMock()
        docker_mock.login.side_effect = raise_error

        with self.assertRaises(InvalidImageRegistryError) as context:
            docker_client = DockerClient(docker_mock)
            docker_client.login(test_registry, 'test_username', 'test_password')
        self.assertEqual(context.exception.kwargs['registry'], test_registry)

    def test_client_login(self) -> None:
        """
        Ensure that login information is properly passed.
        """
        test_registry = 'test_registry'
        test_username = 'test_username'
        test_password = 'test_password'

        docker_mock = MagicMock()
        docker_client = DockerClient(docker_mock)
        docker_client.login(test_registry, test_username, test_password)

        docker_mock.login.assert_called_once_with(
            username=test_username,
            password=test_password,
            registry=test_registry
        )

    @patch('rigelcore.clients.docker.DockerClient.print_logs')
    def test_client_image_push(self, print_mock: Mock) -> None:
        """
        Ensure that the deploy of Docker images works as expected.
        """
        test_image = 'test_image'

        docker_mock_return_value = 'TestImageObject'
        docker_mock = MagicMock()
        docker_mock.push.return_value = docker_mock_return_value

        docker_client = DockerClient(docker_mock)
        docker_client.push(test_image)

        docker_mock.push.assert_called_once_with(
            test_image,
            stream=True,
            decode=True,
        )
        print_mock.assert_called_once_with(docker_mock_return_value)

    @patch('rigelcore.clients.docker.DockerLogPrinter.log')
    def test_docker_operation_error(self, logger_mock: Mock) -> None:
        """
        Ensure that DockerOperationError is thrown whenever an error log is found.
        """
        test_error_message = 'Test error log message.'
        log = {'error': test_error_message}

        image_mock = MagicMock()
        image_mock.__iter__.return_value = [log]

        with self.assertRaises(DockerOperationError) as context:
            docker_client = DockerClient(MagicMock())
            docker_client.print_logs(image_mock)
        self.assertEqual(context.exception.kwargs['msg'], test_error_message)

        logger_mock.assert_called_once_with(log)


if __name__ == '__main__':
    unittest.main()