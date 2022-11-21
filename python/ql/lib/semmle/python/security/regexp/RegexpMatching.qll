/**
 * Provides predicates for reasoning about which strings are matched by a regular expression,
 * and for testing which capture groups are filled when a particular regexp matches a string.
 */

private import semmle.python.RegexTreeView::RegexTreeView as TreeView
// RegexpMatching should be used directly from the shared pack, and not from this file.
deprecated import codeql.regex.nfa.RegexpMatching::Make<TreeView> as Dep
import Dep
