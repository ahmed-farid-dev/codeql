// generated by codegen/codegen.py
private import codeql.swift.generated.Synth
private import codeql.swift.generated.Raw
import codeql.swift.elements.expr.ClosureExpr
import codeql.swift.elements.expr.Expr
import codeql.swift.elements.decl.PatternBindingDecl

module Generated {
  class CaptureListExpr extends Synth::TCaptureListExpr, Expr {
    override string getAPrimaryQlClass() { result = "CaptureListExpr" }

    /**
     * Gets the `index`th binding declaration of this capture list expression (0-based).
     *
     * This includes nodes from the "hidden" AST. It can be overridden in subclasses to change the
     * behavior of both the `Immediate` and non-`Immediate` versions.
     */
    PatternBindingDecl getImmediateBindingDecl(int index) {
      result =
        Synth::convertPatternBindingDeclFromRaw(Synth::convertCaptureListExprToRaw(this)
              .(Raw::CaptureListExpr)
              .getBindingDecl(index))
    }

    /**
     * Gets the `index`th binding declaration of this capture list expression (0-based).
     */
    final PatternBindingDecl getBindingDecl(int index) {
      result = getImmediateBindingDecl(index).resolve()
    }

    /**
     * Gets any of the binding declarations of this capture list expression.
     */
    final PatternBindingDecl getABindingDecl() { result = getBindingDecl(_) }

    /**
     * Gets the number of binding declarations of this capture list expression.
     */
    final int getNumberOfBindingDecls() { result = count(getABindingDecl()) }

    /**
     * Gets the closure body of this capture list expression.
     *
     * This includes nodes from the "hidden" AST. It can be overridden in subclasses to change the
     * behavior of both the `Immediate` and non-`Immediate` versions.
     */
    ClosureExpr getImmediateClosureBody() {
      result =
        Synth::convertClosureExprFromRaw(Synth::convertCaptureListExprToRaw(this)
              .(Raw::CaptureListExpr)
              .getClosureBody())
    }

    /**
     * Gets the closure body of this capture list expression.
     */
    final ClosureExpr getClosureBody() { result = getImmediateClosureBody().resolve() }
  }
}