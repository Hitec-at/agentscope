# -*- coding: utf-8 -*-
"""Model wrapper for post-based inference apis."""
import json
import os
import time
from abc import ABC
from typing import Any, Union, Sequence, List

import requests
from loguru import logger

from .model import ModelWrapperBase, ModelResponse
from ..constants import _DEFAULT_MAX_RETRIES
from ..constants import _DEFAULT_MESSAGES_KEY
from ..constants import _DEFAULT_RETRY_INTERVAL
from ..message import MessageBase
from ..utils.tools import _convert_to_str


class PostAPIModelWrapperBase(ModelWrapperBase, ABC):
    """The base model wrapper for the model deployed on the POST API."""

    model_type: str = "post_api"

    def __init__(
        self,
        config_name: str,
        api_url: str,
        headers: dict = None,
        max_length: int = 2048,
        timeout: int = 30,
        json_args: dict = None,
        post_args: dict = None,
        max_retries: int = _DEFAULT_MAX_RETRIES,
        messages_key: str = _DEFAULT_MESSAGES_KEY,
        retry_interval: int = _DEFAULT_RETRY_INTERVAL,
        **kwargs: Any,
    ) -> None:
        """Initialize the model wrapper.

        Args:
            config_name (`str`):
                The id of the model.
            api_url (`str`):
                The url of the post request api.
            headers (`dict`, defaults to `None`):
                The headers of the api. Defaults to None.
            max_length (`int`, defaults to `2048`):
                The maximum length of the model.
            timeout (`int`, defaults to `30`):
                The timeout of the api. Defaults to 30.
            json_args (`dict`, defaults to `None`):
                The json arguments of the api. Defaults to None.
            post_args (`dict`, defaults to `None`):
                The post arguments of the api. Defaults to None.
            max_retries (`int`, defaults to `3`):
                The maximum number of retries when the `parse_func` raise an
                exception.
            messages_key (`str`, defaults to `inputs`):
                The key of the input messages in the json argument.
            retry_interval (`int`, defaults to `1`):
                The interval between retries when a request fails.

        Note:
            When an object of `PostApiModelWrapper` is called, the arguments
            will of post requests will be used as follows:

            .. code-block:: python

                request.post(
                    url=api_url,
                    headers=headers,
                    json={
                        messages_key: messages,
                        **json_args
                    },
                    **post_args
                )
        """
        super().__init__(config_name=config_name)

        self.api_url = api_url
        self.headers = headers
        self.max_length = max_length
        self.timeout = timeout
        self.json_args = json_args or {}
        self.post_args = post_args or {}
        self.max_retries = max_retries
        self.messages_key = messages_key
        self.retry_interval = retry_interval
        
        # set api key from kwargs
        api_key_envvar = kwargs.get("api_key_envvar", None)
        api_key_key = kwargs.get("api_key_key", None)
        if api_key_key is not None: # default set to headers
            self.headers[api_key_key] = os.environ.get(api_key_envvar)

    def _parse_response(self, response: dict) -> ModelResponse:
        """Parse the response json data into ModelResponse"""
        return ModelResponse(raw=response)

    def __call__(self, input_: str, **kwargs: Any) -> ModelResponse:
        """Calling the model with requests.post.

        Args:
            input_ (`str`):
                The input string to the model.

        Returns:
            `dict`: A dictionary that contains the response of the model and
            related
            information (e.g. cost, time, the number of tokens, etc.).

        Note:
            `parse_func`, `fault_handler` and `max_retries` are reserved for
            `_response_parse_decorator` to parse and check the response
            generated by model wrapper. Their usages are listed as follows:
                - `parse_func` is a callable function used to parse and check
                the response generated by the model, which takes the response
                as input.
                - `max_retries` is the maximum number of retries when the
                `parse_func` raise an exception.
                - `fault_handler` is a callable function which is called
                when the response generated by the model is invalid after
                `max_retries` retries.
        """
        # step1: prepare keyword arguments
        post_args = {**self.post_args, **kwargs}

        request_kwargs = {
            "url": self.api_url,
            "json": {self.messages_key: input_, **self.json_args},
            "headers": self.headers or {},
            **post_args,
        }

        # step2: prepare post requests
        for i in range(1, self.max_retries + 1):
            response = requests.post(**request_kwargs)

            if response.status_code == requests.codes.ok:
                break

            if i < self.max_retries:
                logger.warning(
                    f"Failed to call the model with "
                    f"requests.codes == {response.status_code}, retry "
                    f"{i + 1}/{self.max_retries} times",
                )
                time.sleep(i * self.retry_interval)

        # step3: record model invocation
        # record the model api invocation, which will be skipped if
        # `FileManager.save_api_invocation` is `False`
        self._save_model_invocation(
            arguments=request_kwargs,
            response=response.json(),
        )

        # step4: parse the response
        if response.status_code == requests.codes.ok:
            return self._parse_response(response.json())
        else:
            logger.error(json.dumps(request_kwargs, indent=4))
            raise RuntimeError(
                f"Failed to call the model with {response.json()}",
            )


class PostAPIChatWrapper(PostAPIModelWrapperBase):
    """A post api model wrapper compatilble with openai chat, e.g., vLLM,
    FastChat."""

    model_type: str = "post_api_chat"

    def _parse_response(self, response: dict) -> ModelResponse:
        return ModelResponse(
            text=response["data"]["response"]["choices"][0]["message"][
                "content"
            ],
        )

    def format(
        self,
        *args: Union[MessageBase, Sequence[MessageBase]],
    ) -> Union[List[dict]]:
        """Format the input messages into a list of dict, which is
        compatible to OpenAI Chat API.

        Args:
            args (`Union[MessageBase, Sequence[MessageBase]]`):
                The input arguments to be formatted, where each argument
                should be a `Msg` object, or a list of `Msg` objects.
                In distribution, placeholder is also allowed.

        Returns:
            `Union[List[dict]]`:
                The formatted messages.
        """
        messages = []
        for arg in args:
            if arg is None:
                continue
            if isinstance(arg, MessageBase):
                messages.append(
                    {
                        "role": arg.role,
                        "name": arg.name,
                        "content": _convert_to_str(arg.content),
                    },
                )
            elif isinstance(arg, list):
                messages.extend(self.format(*arg))
            else:
                raise TypeError(
                    f"The input should be a Msg object or a list "
                    f"of Msg objects, got {type(arg)}.",
                )

        return messages


class PostAPIDALLEWrapper(PostAPIModelWrapperBase):
    """A post api model wrapper compatible with openai dall_e"""

    model_type: str = "post_api_dall_e"

    deprecated_model_type: str = "post_api_dalle"

    def _parse_response(self, response: dict) -> ModelResponse:
        if "data" not in response["data"]["response"]:
            if "error" in response["data"]["response"]:
                error_msg = response["data"]["response"]["error"]["message"]
            else:
                error_msg = response["data"]["response"]
            logger.error(f"Error in API call:\n{error_msg}")
            raise ValueError(f"Error in API call:\n{error_msg}")
        urls = [img["url"] for img in response["data"]["response"]["data"]]
        return ModelResponse(image_urls=urls)

    def format(
        self,
        *args: Union[MessageBase, Sequence[MessageBase]],
    ) -> Union[List[dict], str]:
        raise RuntimeError(
            f"Model Wrapper [{type(self).__name__}] doesn't "
            f"need to format the input. Please try to use the "
            f"model wrapper directly.",
        )
