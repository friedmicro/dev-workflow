TARGET_GO_VERSION=1.27
DEV_DIR=$(cat serpentdevflowconfig.yaml | yq .repo_local_location)
cd $DEV_DIR
for dir in $(find . -name "go.mod" | sed 's/.\{7\}$//'); do
	echo $dir
	cd $dir
	go mod edit -go=$TARGET_GO_VERSION
	go get -u ./..
	go mod tidy
	cd $DEV_DIR
done
