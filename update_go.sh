DEV_DIR=$(cat serpentdevflowconfig.yaml | yq .repo_local_location)
cd $DEV_DIR
for dir in $(find . -name "go.mod" | sed 's/.\{7\}$//'); do
	echo $dir
	cd $dir
	go get -u ./...
	cd $DEV_DIR
done
