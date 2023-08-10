all: package-lock.json dist/index.js

package-lock.json: package.json
	npm install

dist/index.js: index.js package-lock.json
	npm run build
