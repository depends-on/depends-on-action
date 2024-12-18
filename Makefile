all: dist/index.js

dist/index.js: index.js package.json
	ls -l index.js package.json dist/index.js
	npm install
	npm run build

package-lock.json: package.json
	npm install

clean:
	rm -rf node_modules dist package-lock.json

.PHONY: all clean
