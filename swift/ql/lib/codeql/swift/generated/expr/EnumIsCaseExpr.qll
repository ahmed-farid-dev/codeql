// generated by codegen/codegen.py
private import codeql.swift.generated.Synth
private import codeql.swift.generated.Raw
import codeql.swift.elements.decl.EnumElementDecl
import codeql.swift.elements.expr.Expr

class EnumIsCaseExprBase extends Synth::TEnumIsCaseExpr, Expr {
  override string getAPrimaryQlClass() { result = "EnumIsCaseExpr" }

  Expr getImmediateSubExpr() {
    result =
      Synth::convertExprFromRaw(Synth::convertEnumIsCaseExprToRaw(this)
            .(Raw::EnumIsCaseExpr)
            .getSubExpr())
  }

  final Expr getSubExpr() { result = getImmediateSubExpr().resolve() }

  EnumElementDecl getImmediateElement() {
    result =
      Synth::convertEnumElementDeclFromRaw(Synth::convertEnumIsCaseExprToRaw(this)
            .(Raw::EnumIsCaseExpr)
            .getElement())
  }

  final EnumElementDecl getElement() { result = getImmediateElement().resolve() }
}
