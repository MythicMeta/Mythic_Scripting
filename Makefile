all_tests:
	python3 -m pytest tests --runslow --asyncio-mode=auto

not_slow:
	python3 -m pytest tests -rs --asyncio-mode=auto

slow:
	python3 -m pytest tests --runslow --asyncio-mode=auto

clean:
	find . -name "*.pyc" -delete
	find . -name "__pycache__" | xargs -I {} rm -rf {}
	rm -rf ./.pytest_cache
	rm -rf ./gql.egg-info
	rm -rf ./dist
	rm -rf ./build
