@echo off
if exist vendor\modules.txt (
  type %CODEQL_EXTRACTOR_GO_ROOT%\codeql-tools\baseline-config-vendor.json
) else (
  type %CODEQL_EXTRACTOR_GO_ROOT%\codeql-tools\baseline-config-empty.json
)
