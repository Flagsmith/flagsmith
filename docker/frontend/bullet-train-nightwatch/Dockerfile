# ---------------------------------------------------------------- #
#                         Dockerfile                               #
# ---------------------------------------------------------------- #
# image:    bullet-train-nightwatch                                #
# name:     kylessg/bullet-train-nightwatch                        #
# desciption: Used for bullet-train e2e tests                      #
# repo:     https://github.com/Flagsmith/bullet-train-frontend #
# authors:  kyle-ssg                                               #
# ---------------------------------------------------------------- #

FROM node:12
LABEL maintainer="kyle.johnson@bullet-train.io"

RUN apt-get update
RUN apt-get install -y openjdk-8-jdk
RUN wget https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_85.0.4183.102-1_amd64.deb
RUN apt install -y ./google-chrome*.deb -f
RUN apt-get clean

CMD ["/bin/bash"]
