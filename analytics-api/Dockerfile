# Build stage
FROM golang:1.25.1-alpine AS builder

WORKDIR /app

COPY go.mod ./

COPY go.sum* ./

RUN go mod download

COPY . .

RUN CGO_ENABLED=0 GOOS=linux go build -o /analytics-api ./cmd/api

# Runtime stage
FROM alpine:latest

RUN apk --no-cache add ca-certificates

WORKDIR /root/

COPY --from=builder /analytics-api .

EXPOSE 8003

CMD ["./analytics-api"]
