from typing import Type

from mypy.mro import calculate_mro, MroError
from mypy.nodes import Block, ClassDef, GDEF, SymbolTable, SymbolTableNode, TypeInfo
from mypy.plugin import DynamicClassDefContext, Plugin
from mypy.types import Instance


class StrappSqlalchemyPlugin(Plugin):
    def get_dynamic_class_hook(self, fullname: str):
        if fullname == "strapp.sqlalchemy.model_base.declarative_base":
            return _dynamic_class_hook
        return None


def _dynamic_class_hook(ctx: DynamicClassDefContext) -> None:
    """Generate a TypedBase class when the declarative_base() is called.
    """
    cls = ClassDef(ctx.name, Block([]))
    cls.fullname = ctx.api.qualified_name(ctx.name)

    info = TypeInfo(SymbolTable(), cls, ctx.api.cur_mod_id)
    cls.info = info
    sym = ctx.api.lookup_fully_qualified_or_none("strapp.sqlalchemy.model_base.DeclarativeMeta")
    assert sym is not None and isinstance(sym.node, TypeInfo)  # nosec
    info.declared_metaclass = info.metaclass_type = Instance(sym.node, [])

    info.bases = [ctx.api.named_type("builtins.object")]

    try:
        calculate_mro(info)
    except MroError:
        info.bases = [ctx.api.named_type("builtins.object")]
        info.fallback_to_any = True

    ctx.api.add_symbol_table_node(ctx.name, SymbolTableNode(GDEF, info))


def plugin(_: str) -> Type[StrappSqlalchemyPlugin]:
    return StrappSqlalchemyPlugin
