
clean:
	find ./properties_cache | grep '.pyc$$' | xargs -I {} rm {}

test: clean
ifndef MODULE
	@echo BTW, you may specify -e MODULE attribute to test specific module/class/test
endif
	cd properties_cache && PYTHONPATH=.:.. python runtests.py $(MODULE)
