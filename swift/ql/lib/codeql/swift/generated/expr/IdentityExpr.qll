// generated by codegen/codegen.py
private import codeql.swift.generated.Synth
private import codeql.swift.generated.Raw
import codeql.swift.elements.expr.Expr

class IdentityExprBase extends Synth::TIdentityExpr, Expr {
  Expr getImmediateSubExpr() {
    result =
      Synth::convertExprFromRaw(Synth::convertIdentityExprToRaw(this)
            .(Raw::IdentityExpr)
            .getSubExpr())
  }

  final Expr getSubExpr() { result = getImmediateSubExpr().resolve() }
}