// generated by codegen/codegen.py
private import codeql.swift.generated.Synth
private import codeql.swift.generated.Raw
import codeql.swift.elements.expr.SelfApplyExpr

class DotSyntaxCallExprBase extends Synth::TDotSyntaxCallExpr, SelfApplyExpr {
  override string getAPrimaryQlClass() { result = "DotSyntaxCallExpr" }
}