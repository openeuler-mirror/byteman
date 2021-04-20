Name:             byteman
Version:          4.0.4
Release:          6
Summary:          Injection of track and test into Java programs
License:          LGPLv2+
URL:              https://byteman.jboss.org/
Source0:          https://github.com/bytemanproject/byteman/archive/%{version}.tar.gz
BuildArch:        noarch

BuildRequires:    java-11-openjdk-devel maven-local maven-shade-plugin
BuildRequires:    maven-source-plugin maven-plugin-plugin maven-plugin-bundle
BuildRequires:    maven-assembly-plugin maven-failsafe-plugin maven-jar-plugin
BuildRequires:    maven-surefire-plugin maven-surefire-provider-testng
BuildRequires:    maven-surefire-provider-junit maven-verifier-plugin
BuildRequires:    maven-dependency-plugin java_cup jarjar objectweb-asm junit testng
BuildRequires:    mvn(org.jboss.modules:jboss-modules)
Provides:         bundled(objectweb-asm) = 6.2 bundled(java_cup) = 1:0.11b-8
Requires:         java-headless >= 1:1.8
Patch0000:        remove_submit_integration_test_verification.patch
Patch0001:        0001-update-ASM-to-eat-jdk12-bytecode.patch

%description
Byteman is a tool which makes it easy to trace, monitor and test the behaviour \
of Java application and JDK runtime code. It injects Java code into your application \
methods or into Java runtime methods without the need for you to recompile, repackage \
or even redeploy your application. Injection can be performed at JVM startup or after \
startup while the application is still running. Injected code can access any of your data \
and call any application methods, including where they are private. You can inject code \
almost anywhere you want and there is no need to prepare the original source code in advance.

%package help
Summary:          API help documentation for byteman
Provides:         byteman-javadoc = %{version}-%{release}
Obsoletes:        byteman-javadoc < %{version}-%{release}
%description help
This package contains the API help documentation for byteman.

%package rulecheck-maven-plugin
Summary:          Plugin for checking rules
%description rulecheck-maven-plugin
This package contains the rule check maven plugin.

%package bmunit
Summary:          Integration of TestNG and JUnit integration
%description bmunit
The Byteman BMUnit package integrates Byteman with JUnit and TestNG making it easy for you \
to use Byteman to extend the range of your unit and integration tests.

%package dtest
Summary:          Remote instrumented testing.

%description dtest
This package provides The Byteman dtest jar, which supports instrumentation of test code executed on \
remote server hosts and validation of assertions describing the expected operation of the instrumented methods.

%prep
%setup -q -n byteman-%{version}

for p in agent/pom.xml tests/pom.xml;
do

for s in "s|net.sf.squirrel-sql.thirdparty-non-maven|java_cup|" "s|java-cup|java_cup|"; do
sed -i ${s} ${p}
done

done

for id in submit.TestSubmit submit.TestSubmit.compiled; do
%pom_xpath_remove "pom:build/pom:plugins/pom:plugin[pom:artifactId='maven-failsafe-plugin']/pom:executions/pom:execution[pom:id='${id}']" agent
done
%patch0000 -p2
%patch0001 -p1

for id in submit.TestSubmit submit.TestSubmit.compiled; do
%pom_xpath_remove "pom:build/pom:plugins/pom:plugin[pom:artifactId='maven-failsafe-plugin']/pom:executions/pom:execution[pom:id='${id}']" tests
done

for p in scope systemPath; do
%pom_xpath_remove "pom:profiles/pom:profile/pom:dependencies/pom:dependency[pom:artifactId='tools']/pom:${p}" install
done

for p in "pom:profiles/pom:profile/pom:dependencies/pom:dependency[pom:artifactId='tools']/pom:scope" \
         "pom:profiles/pom:profile/pom:dependencies/pom:dependency[pom:artifactId='tools']/pom:systemPath" \
         "pom:build/pom:plugins/pom:plugin[pom:artifactId='maven-surefire-plugin']/pom:executions";
do
%pom_xpath_remove "${p}" contrib/bmunit
done

%pom_xpath_set "pom:build/pom:plugins/pom:plugin[pom:artifactId='maven-surefire-plugin']/pom:configuration" '<skip>true</skip>' contrib/bmunit

for d in download docs; do
%pom_disable_module ${d}
done

%pom_remove_plugin -r :maven-javadoc-plugin
%pom_xpath_remove 'pom:execution[pom:id="make-javadoc-assembly"]' byteman

%mvn_package ":byteman-rulecheck-maven-plugin" rulecheck-maven-plugin
%mvn_package ":byteman-bmunit" bmunit
%mvn_package ":byteman-dtest" dtest

%build
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk
%mvn_build --xmvn-javadoc --skipTests

%install
%mvn_install
mkdir -p -m 755 $RPM_BUILD_ROOT%{_bindir}
mkdir -p -m 755 $RPM_BUILD_ROOT%{_datadir}/byteman
mkdir -p -m 755 $RPM_BUILD_ROOT%{_datadir}/byteman/{lib,bin}

for f in bmsubmit bmjava bminstall bmcheck; do
install -m 755 bin/${f}.sh $RPM_BUILD_ROOT%{_datadir}/byteman/bin/${f}
cat > $RPM_BUILD_ROOT%{_bindir}/${f} << EOF
#!/bin/sh

export BYTEMAN_HOME=/usr/share/byteman
export JAVA_HOME=/usr/lib/jvm/java

\$BYTEMAN_HOME/bin/${f} \$*
EOF
done

chmod 755 $RPM_BUILD_ROOT%{_bindir}/*
for m in bmunit dtest install sample submit; do
  ln -s %{_javadir}/byteman/byteman-${m}.jar $RPM_BUILD_ROOT%{_datadir}/byteman/lib/byteman-${m}.jar
done

mkdir -p -m 755 $RPM_BUILD_ROOT%{_datadir}/byteman/contrib
mkdir -p -m 755 $RPM_BUILD_ROOT%{_datadir}/byteman/contrib/jboss-modules-system
ln -s %{_javadir}/byteman/byteman-jboss-modules-plugin.jar $RPM_BUILD_ROOT%{_datadir}/byteman/contrib/jboss-modules-system/byteman-jboss-modules-plugin.jar
ln -s %{_javadir}/byteman/byteman.jar $RPM_BUILD_ROOT%{_datadir}/byteman/lib/byteman.jar

%check
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk
xmvn test --batch-mode --offline verify

%files -f .mfiles
%{_datadir}/byteman/lib/*
%exclude %{_datadir}/byteman/lib/byteman-bmunit.jar
%exclude %{_datadir}/byteman/lib/byteman-dtest.jar
%{_datadir}/byteman/contrib/*
%{_datadir}/byteman/bin/*
%{_bindir}/*
%license docs/copyright.txt

%files help -f .mfiles-javadoc
%doc README

%files rulecheck-maven-plugin -f .mfiles-rulecheck-maven-plugin

%files bmunit -f .mfiles-bmunit
%{_datadir}/byteman/lib/byteman-bmunit.jar

%files dtest -f .mfiles-dtest
%{_datadir}/byteman/lib/byteman-dtest.jar

%changelog
* Fri Apr 16 2021 maminjie <maminjie1@huawei.com> - 4.0.4-6
- Move the test to the %check stage

* Mon Sep 14 2020 huanghaitao <huanghaitao8@huawei.com> - 4.0.4-5
- update ASM to eat jdk bytecode

* Mon May 11 2020 Senlin Xia <xiasenlin1@huawei.com> - 4.0.4-4
- update openjdk and use xmvn-javadoc for maven-javadoc-plugin

* Tue Feb 25 2020 Songshuaishuai <songshuaishuai2@huawei.com> - 4.0.4-3
- Package init
