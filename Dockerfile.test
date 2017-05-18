FROM kartoza/osm-reporter

RUN pip install nose nosexcover
ENV PYTHONPATH=/reporter
CMD ["nosetests", "-v", "--with-id", "--with-xcoverage", "--with-xunit", "--verbose", "--cover-package=reporter", "reporter"]
