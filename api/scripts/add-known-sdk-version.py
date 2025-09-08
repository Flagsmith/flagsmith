import argparse
import typing

import libcst as cst
from libcst.codemod import (
    CodemodCommand,
    CodemodContext,
    diff_code,
    exec_transform_with_prettyprint,
)

MODULE_PATH = "app_analytics/constants.py"
VAR_NAME = "SDK_USER_AGENT_KNOWN_VERSIONS"


class AddKnownSDKVersion(CodemodCommand):
    """
    Update an existing SDK key in SDK_USER_AGENT_KNOWN_VERSIONS to include
    a version. Always ensures "unknown" is first, and there are no duplicates.
    Does not create new SDK keys — you'll have to do that manually.
    """

    DESCRIPTION = "Add a known SDK version to an existing constants entry."

    def __init__(
        self,
        context: CodemodContext,
        sdk: str,
        version: str,
    ) -> None:
        self.context = context
        self.sdk = sdk
        self.version = version

    @staticmethod
    def add_args(parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--sdk",
            required=True,
            help="SDK name, e.g. `flagsmith-js-sdk`",
        )
        parser.add_argument(
            "--version",
            required=True,
            help="SDK version to add, e.g. `9.3.1`",
        )

    def transform_module_impl(self, tree: cst.Module) -> cst.Module:
        new_module_body: list[cst.BaseStatement] = []

        for statement in tree.body:
            if not (
                isinstance(statement, cst.SimpleStatementLine)
                and len(statement.body) == 1
                and isinstance(constant := statement.body[0], cst.AnnAssign)
                and isinstance(constant.target, cst.Name)
                and constant.target.value == VAR_NAME
                and isinstance(constant.value, cst.Dict)
            ):
                new_module_body.append(statement)
                continue

            original_dict: cst.Dict = constant.value
            new_dict_elements: list[cst.DictElement] = []

            for dict_element in original_dict.elements:
                if isinstance(dict_element, cst.DictElement):
                    new_dict_elements.append(self._get_dict_element(dict_element))

            new_module_body.append(
                statement.with_changes(
                    body=[
                        constant.with_changes(
                            value=original_dict.with_changes(
                                elements=new_dict_elements,
                            )
                        )
                    ]
                )
            )

        return tree.with_changes(body=new_module_body)

    @staticmethod
    def _string_value(node: cst.BaseExpression) -> typing.Optional[str]:
        if isinstance(node, cst.SimpleString):
            return str(node.evaluated_value)
        return None

    @staticmethod
    def _quoted_string(value: str) -> cst.SimpleString:
        return cst.SimpleString(f'"{value}"')

    def _get_dict_element(self, dict_element: cst.DictElement) -> cst.DictElement:
        if self._string_value(dict_element.key) == self.sdk:
            existing_versions: list[str] = []
            if isinstance(dict_element.value, cst.List):
                for list_element in dict_element.value.elements:
                    if (
                        string_val := self._string_value(list_element.value)
                    ) is not None:
                        existing_versions.append(string_val)

            normalized_versions: list[str] = ["unknown"]
            for version_str in existing_versions:
                if version_str not in ("unknown", self.version):
                    normalized_versions.append(version_str)
            if self.version not in existing_versions:
                normalized_versions.append(self.version)

            new_list = cst.List(
                [
                    cst.Element(self._quoted_string(version), comma=cst.Comma())
                    for version in normalized_versions
                ]
            )
            return dict_element.with_changes(value=new_list)

        return dict_element


def main() -> None:
    parser = argparse.ArgumentParser(description=AddKnownSDKVersion.DESCRIPTION)
    AddKnownSDKVersion.add_args(parser)
    args = parser.parse_args()
    context = CodemodContext()
    codemod = AddKnownSDKVersion(
        context=context,
        sdk=args.sdk,
        version=args.version,
    )
    code = open(MODULE_PATH).read()
    if result := exec_transform_with_prettyprint(
        codemod,
        code,
    ):
        print(diff_code(code, result, 1))
        with open(MODULE_PATH, "w") as f:
            f.write(result)


if __name__ == "__main__":
    main()
