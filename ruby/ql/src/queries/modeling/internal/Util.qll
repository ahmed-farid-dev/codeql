/**
 * Contains utility methods and classes to assist with generating data extensions models.
 */

private import ruby
private import codeql.ruby.ApiGraphs

/**
 * A file that is relevant in the context of library modeling.
 *
 * In practice, this means a file that is not part of test code.
 */
class RelevantFile extends File {
  RelevantFile() { not this.getRelativePath().regexpMatch(".*/?test(case)?s?/.*") }
}

/**
 * Gets an access path of an argument corresponding to the given `paramNode`.
 */
string getArgumentPath(DataFlow::ParameterNode paramNode) {
  paramNode.getLocation().getFile() instanceof RelevantFile and
  exists(Ast::Parameter param, string paramSpecifier |
    param = paramNode.asParameter() and
    (
      paramSpecifier = param.getPosition().toString()
      or
      paramSpecifier = param.(Ast::KeywordParameter).getName() + ":"
      or
      param instanceof Ast::BlockParameter and
      paramSpecifier = "block"
    )
  |
    result = "Argument[" + paramSpecifier + "]"
  )
}

/**
 * Holds if `(type,path)` evaluates to the given method, when evalauted from a client of the current library.
 */
predicate pathToMethod(DataFlow::MethodNode method, string type, string path) {
  method.getLocation().getFile() instanceof RelevantFile and
  exists(DataFlow::ModuleNode mod, string methodName |
    method = mod.getOwnInstanceMethod(methodName) and
    if methodName = "initialize"
    then (
      type = mod.getQualifiedName() + "!" and
      path = "Method[new]"
    ) else (
      type = mod.getQualifiedName() and
      path = "Method[" + methodName + "]"
    )
    or
    method = mod.getOwnSingletonMethod(methodName) and
    type = mod.getQualifiedName() + "!" and
    path = "Method[" + methodName + "]"
  )
}

/** Gets any parameter to `method`. This may be a positional, keyword, or block parameter. */
private DataFlow::ParameterNode getAnyParameter(DataFlow::MethodNode method) {
  result = [method.getParameter(_), method.getKeywordParameter(_), method.getBlockParameter()]
}

private predicate pathToNodeBase(API::Node node, string type, string path, boolean isOutput) {
  exists(DataFlow::MethodNode method, string prevPath | pathToMethod(method, type, prevPath) |
    isOutput = true and
    node = method.getAReturnNode().backtrack() and
    path = prevPath + ".ReturnValue" and
    not method.getMethodName() = "initialize" // ignore return value of initialize method
    or
    isOutput = false and
    exists(DataFlow::ParameterNode paramNode |
      paramNode = getAnyParameter(method) and
      node = paramNode.track()
    |
      path = prevPath + "." + getArgumentPath(paramNode)
    )
  )
}

private predicate pathToNodeRec(
  API::Node node, string type, string path, boolean isOutput, int pathLength
) {
  pathLength < 8 and
  (
    pathToNodeBase(node, type, path, isOutput) and
    pathLength = 1
    or
    exists(API::Node prevNode, string prevPath, boolean prevIsOutput, int prevPathLength |
      pathToNodeRec(prevNode, type, prevPath, prevIsOutput, prevPathLength) and
      pathLength = prevPathLength + 1
    |
      node = prevNode.getAnElement() and
      path = prevPath + ".Element" and
      isOutput = prevIsOutput
      or
      node = prevNode.getReturn() and
      path = prevPath + ".ReturnValue" and
      isOutput = prevIsOutput
      or
      prevIsOutput = false and
      isOutput = true and
      (
        exists(int n |
          node = prevNode.getParameter(n) and
          path = prevPath + ".Parameter[" + n + "]"
        )
        or
        exists(string name |
          node = prevNode.getKeywordParameter(name) and
          path = prevPath + ".Parameter[" + name + ":]"
        )
        or
        node = prevNode.getBlock() and
        path = prevPath + ".Parameter[block]"
      )
    )
  )
}

/**
 * Holds if `(type,path)` evaluates to a value corresponding to `node`, when evaluated from a client of the current library.
 */
predicate pathToNode(API::Node node, string type, string path, boolean isOutput) {
  pathToNodeRec(node, type, path, isOutput, _)
}
