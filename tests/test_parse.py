# pyright: reportPrivateUsage=false

from importlib import import_module

from networkx import DiGraph

from pydantic2zod._model import (
    ClassDecl,
    ClassField,
    GenericType,
    PrimitiveType,
    UnionType,
    UserDefinedType,
)
from pydantic2zod._parser import _ParseModule, parse


def test_recurses_into_imported_modules():
    m = import_module("tests.fixtures.external")

    classes = parse(m)

    assert classes == [
        ClassDecl(
            name="Class",
            full_path="tests.fixtures.all_in_one.Class",
            fields=[
                ClassField(name="name", type=PrimitiveType(name="str")),
                ClassField(
                    name="methods",
                    type=GenericType(
                        generic="list", type_vars=[PrimitiveType(name="str")]
                    ),
                ),
            ],
            base_classes=["BaseModel"],
        ),
        ClassDecl(
            name="DataClass",
            full_path="tests.fixtures.all_in_one.DataClass",
            fields=[ClassField(name="frozen", type=PrimitiveType(name="bool"))],
            base_classes=["Class"],
        ),
        ClassDecl(
            name="Module",
            full_path="tests.fixtures.external.Module",
            fields=[
                ClassField(name="name", type=PrimitiveType(name="str")),
                ClassField(
                    name="classes",
                    type=GenericType(
                        generic="list", type_vars=[UserDefinedType(name="DataClass")]
                    ),
                ),
            ],
            base_classes=["BaseModel"],
        ),
    ]


class TestParseModule:
    def test_parses_all_pydantic_models_within_the_same_module(self):
        """
        - parses pydantic models
        - skips non-pydantic classes
        """
        classes = (
            _ParseModule(import_module("tests.fixtures.all_in_one"), DiGraph())
            .exec()
            .classes()
        )

        assert classes == [
            ClassDecl(
                name="Class",
                full_path="tests.fixtures.all_in_one.Class",
                base_classes=["BaseModel"],
                fields=[
                    ClassField(name="name", type=PrimitiveType(name="str")),
                    ClassField(
                        name="methods",
                        type=GenericType(
                            generic="list", type_vars=[PrimitiveType(name="str")]
                        ),
                    ),
                ],
            ),
            ClassDecl(
                name="DataClass",
                full_path="tests.fixtures.all_in_one.DataClass",
                base_classes=["Class"],
                fields=[
                    ClassField(name="frozen", type=PrimitiveType(name="bool")),
                ],
            ),
            ClassDecl(
                name="Module",
                full_path="tests.fixtures.all_in_one.Module",
                base_classes=["BaseModel"],
                fields=[
                    ClassField(name="name", type=PrimitiveType(name="str")),
                    ClassField(
                        name="classes",
                        type=GenericType(
                            generic="list", type_vars=[UserDefinedType(name="Class")]
                        ),
                    ),
                ],
            ),
        ]

    def test_parses_only_the_models_explicitly_asked(self):
        classes = (
            _ParseModule(
                import_module("tests.fixtures.all_in_one"),
                DiGraph(),
                parse_only_models={"Class"},
            )
            .exec()
            .classes()
        )

        assert set(c.name for c in classes) == {"Class"}

    def test_parses_only_the_models_explicitly_asked_and_their_dependencies(self):
        classes = (
            _ParseModule(
                import_module("tests.fixtures.all_in_one"),
                DiGraph(),
                parse_only_models={"Module"},
            )
            .exec()
            .classes()
        )

        assert set(c.name for c in classes) == {"Class", "Module"}

    def test_detects_external_models(self):
        parse = _ParseModule(import_module("tests.fixtures.external"), DiGraph()).exec()

        assert parse.external_models() == {"tests.fixtures.all_in_one.DataClass"}
        assert parse.classes() == [
            ClassDecl(
                name="Module",
                full_path="tests.fixtures.external.Module",
                base_classes=["BaseModel"],
                fields=[
                    ClassField(name="name", type=PrimitiveType(name="str")),
                    ClassField(
                        name="classes",
                        type=GenericType(
                            generic="list",
                            type_vars=[UserDefinedType(name="DataClass")],
                        ),
                    ),
                ],
            ),
        ]

    def test_supports_explicit_type_alias(self):
        parse = _ParseModule(
            import_module("tests.fixtures.type_alias"), DiGraph()
        ).exec()

        assert parse.classes() == [
            ClassDecl(
                name="Function",
                full_path="tests.fixtures.type_alias.Function",
                fields=[ClassField(name="name", type=PrimitiveType(name="str"))],
                base_classes=["BaseModel"],
            ),
            ClassDecl(
                name="LambdaFunc",
                full_path="tests.fixtures.type_alias.LambdaFunc",
                fields=[
                    ClassField(
                        name="args",
                        type=GenericType(
                            generic="list", type_vars=[PrimitiveType(name="str")]
                        ),
                    )
                ],
                base_classes=["BaseModel"],
            ),
            ClassDecl(
                name="EventBus",
                full_path="tests.fixtures.type_alias.EventBus",
                fields=[
                    ClassField(
                        name="handlers",
                        type=UnionType(
                            types=[
                                UserDefinedType(name="Function"),
                                UserDefinedType(name="LambdaFunc"),
                            ]
                        ),
                    )
                ],
                base_classes=["BaseModel"],
            ),
        ]

    def test_supports_builtin_types(self):
        parse = _ParseModule(
            import_module("tests.fixtures.builtin_types"), DiGraph()
        ).exec()

        assert parse.classes() == [
            ClassDecl(
                name="User",
                full_path="tests.fixtures.builtin_types.User",
                fields=[
                    ClassField(name="id", type=UserDefinedType(name="UUID")),
                    ClassField(name="name", type=PrimitiveType(name="str")),
                ],
                base_classes=["BaseModel"],
            )
        ]
        # built-in types are not considered external models
        assert parse.external_models() == set()

    def test_resolves_import_aliases(self):
        parse = _ParseModule(
            import_module("tests.fixtures.import_alias"), DiGraph()
        ).exec()

        assert parse.classes() == [
            ClassDecl(
                name="Module",
                full_path="tests.fixtures.import_alias.Module",
                fields=[
                    ClassField(name="name", type=PrimitiveType(name="str")),
                    ClassField(
                        name="classes",
                        type=GenericType(
                            generic="list",
                            type_vars=[UserDefinedType(name="Cls")],
                        ),
                    ),
                ],
                base_classes=["BaseModel"],
            )
        ]
        # built-in types are not considered external models
        assert parse.external_models() == set(["tests.fixtures.all_in_one.Class"])
