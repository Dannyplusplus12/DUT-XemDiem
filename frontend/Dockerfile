FROM ghcr.io/cirruslabs/flutter:3.24.3 AS build
WORKDIR /app
COPY . .
RUN flutter config --enable-web
RUN flutter pub get
RUN flutter build web --release

FROM nginx:1.27-alpine
COPY --from=build /app/build/web /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
