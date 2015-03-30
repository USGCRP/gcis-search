@REM ----------------------------------------------------------------------------
@REM  Copyright 2001-2006 The Apache Software Foundation.
@REM
@REM  Licensed under the Apache License, Version 2.0 (the "License");
@REM  you may not use this file except in compliance with the License.
@REM  You may obtain a copy of the License at
@REM
@REM       http://www.apache.org/licenses/LICENSE-2.0
@REM
@REM  Unless required by applicable law or agreed to in writing, software
@REM  distributed under the License is distributed on an "AS IS" BASIS,
@REM  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
@REM  See the License for the specific language governing permissions and
@REM  limitations under the License.
@REM ----------------------------------------------------------------------------
@REM
@REM   Copyright (c) 2001-2006 The Apache Software Foundation.  All rights
@REM   reserved.

@echo off

set ERROR_CODE=0

:init
@REM Decide how to startup depending on the version of windows

@REM -- Win98ME
if NOT "%OS%"=="Windows_NT" goto Win9xArg

@REM set local scope for the variables with windows NT shell
if "%OS%"=="Windows_NT" @setlocal

@REM -- 4NT shell
if "%eval[2+2]" == "4" goto 4NTArgs

@REM -- Regular WinNT shell
set CMD_LINE_ARGS=%*
goto WinNTGetScriptDir

@REM The 4NT Shell from jp software
:4NTArgs
set CMD_LINE_ARGS=%$
goto WinNTGetScriptDir

:Win9xArg
@REM Slurp the command line arguments.  This loop allows for an unlimited number
@REM of arguments (up to the command line limit, anyway).
set CMD_LINE_ARGS=
:Win9xApp
if %1a==a goto Win9xGetScriptDir
set CMD_LINE_ARGS=%CMD_LINE_ARGS% %1
shift
goto Win9xApp

:Win9xGetScriptDir
set SAVEDIR=%CD%
%0\
cd %0\..\.. 
set BASEDIR=%CD%
cd %SAVEDIR%
set SAVE_DIR=
goto repoSetup

:WinNTGetScriptDir
set BASEDIR=%~dp0\..

:repoSetup


if "%JAVACMD%"=="" set JAVACMD=java

if "%REPO%"=="" set REPO=%BASEDIR%\repo

set CLASSPATH="%BASEDIR%"\etc;"%REPO%"\org\openprovenance\prov\prov-xml\0.6.1\prov-xml-0.6.1.jar;"%REPO%"\org\openprovenance\prov\prov-model\0.6.1\prov-model-0.6.1.jar;"%REPO%"\commons-codec\commons-codec\1.9\commons-codec-1.9.jar;"%REPO%"\javax\xml\bind\jaxb-api\2.2.4\jaxb-api-2.2.4.jar;"%REPO%"\javax\xml\stream\stax-api\1.0-2\stax-api-1.0-2.jar;"%REPO%"\javax\activation\activation\1.1\activation-1.1.jar;"%REPO%"\com\sun\xml\bind\jaxb-impl\2.2.6\jaxb-impl-2.2.6.jar;"%REPO%"\commons-lang\commons-lang\2.6\commons-lang-2.6.jar;"%REPO%"\commons-collections\commons-collections\3.2.1\commons-collections-3.2.1.jar;"%REPO%"\org\openprovenance\prov\prov-rdf\0.6.1\prov-rdf-0.6.1.jar;"%REPO%"\org\openrdf\sesame\sesame-runtime\2.6.10\sesame-runtime-2.6.10.jar;"%REPO%"\org\openrdf\sesame\sesame-model\2.6.10\sesame-model-2.6.10.jar;"%REPO%"\org\openrdf\sesame\sesame-query\2.6.10\sesame-query-2.6.10.jar;"%REPO%"\org\openrdf\sesame\sesame-queryalgebra-model\2.6.10\sesame-queryalgebra-model-2.6.10.jar;"%REPO%"\org\openrdf\sesame\sesame-queryparser-api\2.6.10\sesame-queryparser-api-2.6.10.jar;"%REPO%"\org\openrdf\sesame\sesame-queryparser-serql\2.6.10\sesame-queryparser-serql-2.6.10.jar;"%REPO%"\org\openrdf\sesame\sesame-queryparser-sparql\2.6.10\sesame-queryparser-sparql-2.6.10.jar;"%REPO%"\org\openrdf\sesame\sesame-queryresultio-api\2.6.10\sesame-queryresultio-api-2.6.10.jar;"%REPO%"\org\openrdf\sesame\sesame-queryresultio-binary\2.6.10\sesame-queryresultio-binary-2.6.10.jar;"%REPO%"\org\openrdf\sesame\sesame-queryresultio-sparqljson\2.6.10\sesame-queryresultio-sparqljson-2.6.10.jar;"%REPO%"\org\openrdf\sesame\sesame-queryresultio-sparqlxml\2.6.10\sesame-queryresultio-sparqlxml-2.6.10.jar;"%REPO%"\org\openrdf\sesame\sesame-queryresultio-text\2.6.10\sesame-queryresultio-text-2.6.10.jar;"%REPO%"\net\sf\opencsv\opencsv\2.0\opencsv-2.0.jar;"%REPO%"\org\openrdf\sesame\sesame-repository-api\2.6.10\sesame-repository-api-2.6.10.jar;"%REPO%"\org\openrdf\sesame\sesame-repository-manager\2.6.10\sesame-repository-manager-2.6.10.jar;"%REPO%"\org\openrdf\sesame\sesame-repository-event\2.6.10\sesame-repository-event-2.6.10.jar;"%REPO%"\org\openrdf\sesame\sesame-repository-http\2.6.10\sesame-repository-http-2.6.10.jar;"%REPO%"\org\openrdf\sesame\sesame-repository-sail\2.6.10\sesame-repository-sail-2.6.10.jar;"%REPO%"\org\openrdf\sesame\sesame-repository-dataset\2.6.10\sesame-repository-dataset-2.6.10.jar;"%REPO%"\org\openrdf\sesame\sesame-repository-contextaware\2.6.10\sesame-repository-contextaware-2.6.10.jar;"%REPO%"\org\openrdf\sesame\sesame-http-protocol\2.6.10\sesame-http-protocol-2.6.10.jar;"%REPO%"\org\openrdf\sesame\sesame-http-client\2.6.10\sesame-http-client-2.6.10.jar;"%REPO%"\commons-httpclient\commons-httpclient\3.1\commons-httpclient-3.1.jar;"%REPO%"\org\openrdf\sesame\sesame-rio-api\2.6.10\sesame-rio-api-2.6.10.jar;"%REPO%"\org\openrdf\sesame\sesame-rio-binary\2.6.10\sesame-rio-binary-2.6.10.jar;"%REPO%"\org\openrdf\sesame\sesame-rio-ntriples\2.6.10\sesame-rio-ntriples-2.6.10.jar;"%REPO%"\org\openrdf\sesame\sesame-rio-trix\2.6.10\sesame-rio-trix-2.6.10.jar;"%REPO%"\org\openrdf\sesame\sesame-rio-turtle\2.6.10\sesame-rio-turtle-2.6.10.jar;"%REPO%"\org\openrdf\sesame\sesame-sail-api\2.6.10\sesame-sail-api-2.6.10.jar;"%REPO%"\org\openrdf\sesame\sesame-sail-inferencer\2.6.10\sesame-sail-inferencer-2.6.10.jar;"%REPO%"\org\openrdf\sesame\sesame-sail-memory\2.6.10\sesame-sail-memory-2.6.10.jar;"%REPO%"\org\openrdf\sesame\sesame-queryalgebra-evaluation\2.6.10\sesame-queryalgebra-evaluation-2.6.10.jar;"%REPO%"\org\openrdf\sesame\sesame-repository-sparql\2.6.10\sesame-repository-sparql-2.6.10.jar;"%REPO%"\org\openrdf\sesame\sesame-sail-nativerdf\2.6.10\sesame-sail-nativerdf-2.6.10.jar;"%REPO%"\org\openrdf\sesame\sesame-sail-rdbms\2.6.10\sesame-sail-rdbms-2.6.10.jar;"%REPO%"\commons-dbcp\commons-dbcp\1.3\commons-dbcp-1.3.jar;"%REPO%"\commons-pool\commons-pool\1.5.4\commons-pool-1.5.4.jar;"%REPO%"\org\slf4j\slf4j-api\1.6.1\slf4j-api-1.6.1.jar;"%REPO%"\org\openrdf\sesame\sesame-rio-n3\2.6.10\sesame-rio-n3-2.6.10.jar;"%REPO%"\org\openrdf\sesame\sesame-rio-rdfxml\2.6.10\sesame-rio-rdfxml-2.6.10.jar;"%REPO%"\org\openrdf\sesame\sesame-util\2.6.10\sesame-util-2.6.10.jar;"%REPO%"\org\openrdf\sesame\sesame-rio-trig\2.6.10\sesame-rio-trig-2.6.10.jar;"%REPO%"\org\openprovenance\prov\prov-n\0.6.1\prov-n-0.6.1.jar;"%REPO%"\org\antlr\antlr-runtime\3.4\antlr-runtime-3.4.jar;"%REPO%"\antlr\antlr\2.7.7\antlr-2.7.7.jar;"%REPO%"\org\antlr\stringtemplate\4.0.2\stringtemplate-4.0.2.jar;"%REPO%"\org\openprovenance\prov\prov-interop\0.6.1\prov-interop-0.6.1.jar;"%REPO%"\org\openprovenance\prov\prov-dot\0.6.1\prov-dot-0.6.1.jar;"%REPO%"\commons-io\commons-io\2.0.1\commons-io-2.0.1.jar;"%REPO%"\org\openprovenance\prov\prov-json\0.6.1\prov-json-0.6.1.jar;"%REPO%"\com\google\code\gson\gson\2.1\gson-2.1.jar;"%REPO%"\org\openprovenance\prov\prov-template\0.6.1\prov-template-0.6.1.jar;"%REPO%"\org\openprovenance\prov\prov-generator\0.6.1\prov-generator-0.6.1.jar;"%REPO%"\commons-cli\commons-cli\1.0\commons-cli-1.0.jar;"%REPO%"\commons-logging\commons-logging\1.0\commons-logging-1.0.jar;"%REPO%"\org\jboss\resteasy\jaxrs-api\3.0.8.Final\jaxrs-api-3.0.8.Final.jar;"%REPO%"\log4j\log4j\1.2.17\log4j-1.2.17.jar;"%REPO%"\org\openprovenance\prov\toolbox\0.6.1\toolbox-0.6.1.jar
goto endInit

@REM Reaching here means variables are defined and arguments have been captured
:endInit

%JAVACMD% %JAVA_OPTS%  -classpath %CLASSPATH_PREFIX%;%CLASSPATH% -Dapp.name="provconvert" -Dapp.repo="%REPO%" -Dapp.home="%BASEDIR%" -Dbasedir="%BASEDIR%" org.openprovenance.prov.interop.CommandLineArguments %CMD_LINE_ARGS%
if ERRORLEVEL 1 goto error
goto end

:error
if "%OS%"=="Windows_NT" @endlocal
set ERROR_CODE=%ERRORLEVEL%

:end
@REM set local scope for the variables with windows NT shell
if "%OS%"=="Windows_NT" goto endNT

@REM For old DOS remove the set variables from ENV - we assume they were not set
@REM before we started - at least we don't leave any baggage around
set CMD_LINE_ARGS=
goto postExec

:endNT
@REM If error code is set to 1 then the endlocal was done already in :error.
if %ERROR_CODE% EQU 0 @endlocal


:postExec

if "%FORCE_EXIT_ON_ERROR%" == "on" (
  if %ERROR_CODE% NEQ 0 exit %ERROR_CODE%
)

exit /B %ERROR_CODE%
