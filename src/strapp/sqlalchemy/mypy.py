from datetime import datetime
from typing import Callable, Optional, Type

import sqlalchemy.ext.mypy.apply
import sqlalchemy.ext.mypy.decl_class
import sqlalchemy.ext.mypy.plugin
import sqlalchemy.ext.mypy.util
from mypy.nodes import (
    ArgKind,
    AssignmentStmt,
    CallExpr,
    MDEF,
    MemberExpr,
    NameExpr,
    SymbolTableNode,
    TypeInfo,
    Var,
)
from mypy.plugin import ClassDefContext, DynamicClassDefContext, Plugin
from mypy.types import get_proper_type


class StrappSqlalchemyPlugin(Plugin):
    def get_dynamic_class_hook(self, fullname: str):
        if fullname == "strapp.sqlalchemy.model_base.declarative_base":
            return _dynamic_class_hook
        return None

    def get_base_class_hook(self, fullname: str) -> Optional[Callable[[ClassDefContext], None]]:
        sym = self.lookup_fully_qualified(fullname)

        if (
            sym
            and isinstance(sym.node, TypeInfo)
            and sqlalchemy.ext.mypy.util.has_declarative_base(sym.node)
        ):
            return _base_cls_hook

        return None


def _dynamic_class_hook(ctx: DynamicClassDefContext) -> None:
    """Generate a TypedBase class when the declarative_base() is called."""
    sqlalchemy.ext.mypy.plugin._dynamic_class_hook(ctx)  # type: ignore


def _base_cls_hook(ctx: ClassDefContext) -> None:
    api = ctx.api
    cls = ctx.cls

    if cls.keywords.get("created_at"):
        make_dt_assignment(api, cls, "created_at", "CreatedAt")

    if cls.keywords.get("updated_at"):
        make_dt_assignment(api, cls, "updated_at", "UpdatedAt")

    if cls.keywords.get("deleted_at"):
        make_dt_assignment(api, cls, "deleted_at", "DeletedAt")

    # Reexecute the default sqlalchemy handling code, if we get executed it seems
    # to not run theirs(?)
    sqlalchemy.ext.mypy.plugin._add_globals(ctx)  # type: ignore
    sqlalchemy.ext.mypy.decl_class.scan_declarative_assignments_and_apply_types(ctx.cls, ctx.api)


def make_dt_assignment(api, cls, name, base_cls_name):
    """Create a stub column assignment for mypy/sqlalchemy to pick up.

    Due to essentially no documentation on the mypy plugin setup, this is
    pretty much all guesswork. It seems to end up working as far as attribute
    access goes, but is not being picked for type checking on constructor
    arguments, which must be part of the sqlalchemy plugin.
    """
    info = sqlalchemy.ext.mypy.util.info_for_cls(cls, api)

    type_ = get_proper_type(
        api.named_type("sqlalchemy.orm.Mapped", [api.named_type("datetime.datetime")])
    )

    var = Var(name, type_)
    var._fullname = f"{cls.fullname}.{name}"
    var.info = info

    name_expr = NameExpr(name)
    name_expr.node = var

    statement = AssignmentStmt(
        lvalues=[name_expr],
        rvalue=CallExpr(
            callee=MemberExpr(expr=NameExpr("sqlalchemy"), name="Column"),
            args=[
                CallExpr(
                    callee=MemberExpr(
                        expr=MemberExpr(expr=NameExpr("sqlalchemy"), name="types"), name="DateTime",
                    ),
                    args=[],
                    arg_kinds=[],
                    arg_names=[],
                )
            ],
            arg_kinds=[ArgKind.ARG_POS],
            arg_names=[None],
        ),
        type=type_,
    )
    cls.defs.body.append(statement)

    type_ = api.named_type(f"strapp.sqlalchemy.model_base.{base_cls_name}")
    info.bases.append(type_)

    info.names[name] = SymbolTableNode(kind=MDEF, node=var, plugin_generated=True)


def plugin(_: str) -> Type[StrappSqlalchemyPlugin]:
    return StrappSqlalchemyPlugin
