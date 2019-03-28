FROM gcr.io/google_appengine/nodejs

RUN /usr/local/bin/install_node 8.11.0

RUN curl -o- -L https://yarnpkg.com/install.sh | bash

COPY build /app/build
COPY package.json /app/package.json
RUN ~/.yarn/bin/yarn install

# Undo the env variable setting from the google nodejs env.
# We set NODE_ENV ourself when we run the server, rather than have a global
# setting which messes with npm install.
ENV NODE_ENV ''

WORKDIR /app/
EXPOSE 8080

CMD ~/.yarn/bin/yarn run start:prod
