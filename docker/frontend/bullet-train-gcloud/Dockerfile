# ---------------------------------------------------------------- #
#                         Dockerfile                               #
# ---------------------------------------------------------------- #
# image:    bullet-train-gcloud                                    #
# name:     kylessg/bullet-train-gcloud                            #
# desciption: Used to deploy bullet-train to Google App Engine     #
# repo:     https://github.com/Flagsmith/bullet-train-frontend #
# authors:  kyle-ssg                                               #
# ---------------------------------------------------------------- #

FROM node:12-slim
LABEL maintainer="kyle.johnson@bullet-train.io"

RUN apt-get update && apt-get install -y apt-transport-https gnupg curl lsb-release
RUN export CLOUD_SDK_REPO="cloud-sdk-$(lsb_release -c -s)" && \
  echo "cloud SDK repo: $CLOUD_SDK_REPO" && \
  echo "deb http://packages.cloud.google.com/apt $CLOUD_SDK_REPO main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
  curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add - && \
  apt-get update -y && apt-get install google-cloud-sdk -y

CMD ["/bin/bash"]
