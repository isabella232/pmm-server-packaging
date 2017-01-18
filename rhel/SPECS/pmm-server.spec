%global provider	github
%global provider_tld	com
%global project		delgod
%global repo		pmm-server
%global provider_prefix	%{provider}.%{provider_tld}/%{project}/%{repo}
%global import_path	%{provider_prefix}
%global commit		6f661fb799519b69a4c2daf8ea75157acda629c4
%global shortcommit	%(c=%{commit}; echo ${c:0:7})

Name:		%{repo}
Version:	1.0.7
Release:	3%{?dist}
Summary:	Percona Monitoring and Management Server

License:	AGPLv3
URL:		https://%{provider_prefix}
Source0:	https://%{provider_prefix}/archive/%{commit}/%{repo}-%{shortcommit}.tar.gz

BuildArch:	noarch
Requires:	nginx
BuildRequires:	openssl

%description
Percona Monitoring and Management (PMM) Server.
See the PMM docs for more information.


%prep
%setup -q -n %{repo}-%{commit}
sed -i "s/ENV_SERVER_USER/${SERVER_USER:-pmm}/g" prometheus.yml
sed -i "s/ENV_SERVER_PASSWORD/${SERVER_PASSWORD:-pmm}/g" prometheus.yml


%build
echo "${SERVER_USER:-pmm}:$(openssl passwd -apr1 ${SERVER_PASSWORD:-pmm})" > .htpasswd


%install
install -d %{buildroot}%{_sysconfdir}/nginx/conf.d
mv .htpasswd  %{buildroot}%{_sysconfdir}/nginx/.htpasswd
mv nginx.conf %{buildroot}%{_sysconfdir}/nginx/conf.d/pmm.conf
install -d %{buildroot}%{_sysconfdir}/cron.daily
mv purge-qan-data %{buildroot}%{_sysconfdir}/cron.daily/purge-qan-data
install -d %{buildroot}%{_datadir}/percona-dashboards
mv import-dashboards.py %{buildroot}%{_datadir}/percona-dashboards/import-dashboards.py

mv sysconfig %{buildroot}%{_sysconfdir}/sysconfig
mv orchestrator.conf.json %{buildroot}%{_sysconfdir}/orchestrator.conf.json
mv prometheus.yml %{buildroot}%{_sysconfdir}/prometheus.yml
install -d %{buildroot}%{_datadir}/%{name}
cp -pav ./* %{buildroot}%{_datadir}/%{name}


%files
%license LICENSE
%doc README.md CHANGELOG.md
%{_sysconfdir}/sysconfig
%{_sysconfdir}/prometheus.yml
%{_sysconfdir}/nginx/.htpasswd
%{_sysconfdir}/nginx/conf.d/pmm.conf
%{_sysconfdir}/orchestrator.conf.json
%{_sysconfdir}/cron.daily/purge-qan-data
%{_datadir}/percona-dashboards/import-dashboards.py*
%{_datadir}/%{name}


%changelog
* Wed Dec 28 2016 Mykola Marzhan <mykola.marzhan@percona.com> - 1.0.7-2
- add sysconfig

* Mon Dec 19 2016 Mykola Marzhan <mykola.marzhan@percona.com> - 1.0.7-1
- init version