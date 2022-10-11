// generated by codegen/codegen.py
private import codeql.swift.generated.Synth
private import codeql.swift.generated.Raw
import codeql.swift.elements.expr.Expr
import codeql.swift.elements.decl.ParamDecl

class DefaultArgumentExprBase extends Synth::TDefaultArgumentExpr, Expr {
  override string getAPrimaryQlClass() { result = "DefaultArgumentExpr" }

  ParamDecl getImmediateParamDecl() {
    result =
      Synth::convertParamDeclFromRaw(Synth::convertDefaultArgumentExprToRaw(this)
            .(Raw::DefaultArgumentExpr)
            .getParamDecl())
  }

  final ParamDecl getParamDecl() { result = getImmediateParamDecl().resolve() }

  int getParamIndex() {
    result = Synth::convertDefaultArgumentExprToRaw(this).(Raw::DefaultArgumentExpr).getParamIndex()
  }

  Expr getImmediateCallerSideDefault() {
    result =
      Synth::convertExprFromRaw(Synth::convertDefaultArgumentExprToRaw(this)
            .(Raw::DefaultArgumentExpr)
            .getCallerSideDefault())
  }

  final Expr getCallerSideDefault() { result = getImmediateCallerSideDefault().resolve() }

  final predicate hasCallerSideDefault() { exists(getCallerSideDefault()) }
}
