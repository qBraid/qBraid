# Copyright 2026 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Unit tests for  BraketProvider.aws_configure function.

"""

from unittest.mock import patch

from qbraid.runtime.aws.provider import BraketProvider


def test_aws_directory_and_files_creation():
    """Test create AWS dummy configuration files."""
    with (
        patch("pathlib.Path.mkdir") as mock_mkdir,
        patch("pathlib.Path.exists", side_effect=[False, False]),
        patch("pathlib.Path.write_text") as mock_write_text,
    ):
        BraketProvider.aws_configure()
        mock_mkdir.assert_called_once()
        assert mock_write_text.call_count == 2


def test_preservation_of_existing_files():
    """Test if the correct placeholder values are written to the files when they are created."""
    with (
        patch("pathlib.Path.exists", side_effect=[True, True]),
        patch("pathlib.Path.write_text") as mock_write_text,
    ):
        BraketProvider.aws_configure()
        mock_write_text.assert_not_called()


def test_correct_content_in_files():
    """Test if the correct placeholder values are written to the files when they are created."""
    expected_config_content = "[default]\nregion = us-east-1\noutput = json\n"
    expected_credentials_content = (
        "[default]\naws_access_key_id = MYACCESSKEY\naws_secret_access_key = MYSECRETKEY\n"
    )

    with (
        patch("pathlib.Path.exists", side_effect=[False, False]),
        patch("pathlib.Path.write_text") as mock_write_text,
    ):
        BraketProvider.aws_configure(
            aws_access_key_id="MYACCESSKEY", aws_secret_access_key="MYSECRETKEY"
        )
        mock_write_text.assert_any_call(expected_config_content)
        mock_write_text.assert_any_call(expected_credentials_content)
