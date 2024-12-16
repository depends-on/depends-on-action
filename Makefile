all: package-lock.json dist/index.js

package-lock.json: package.json
	npm install

dist/index.js: index.js package-lock.json
	if ! command -v ncc >/dev/null 2>&1; then \
		echo "skip build since ncc is not available"; \
	else \
		npm run build; \
	fi
