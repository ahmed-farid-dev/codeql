// generated by codegen/codegen.py
private import codeql.swift.generated.Synth
private import codeql.swift.generated.Raw
import codeql.swift.elements.expr.BuiltinLiteralExpr

class BooleanLiteralExprBase extends Synth::TBooleanLiteralExpr, BuiltinLiteralExpr {
  override string getAPrimaryQlClass() { result = "BooleanLiteralExpr" }

  boolean getValue() {
    result = Synth::convertBooleanLiteralExprToRaw(this).(Raw::BooleanLiteralExpr).getValue()
  }
}