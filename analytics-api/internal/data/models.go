package data

import (
	"errors"

	"github.com/jackc/pgx/v5/pgxpool"
)

var ErrRecordNotFound = errors.New("record not found")

type Models struct {
	System SystemModel
}

func NewModels(db *pgxpool.Pool) Models {
	return Models{
		System: SystemModel{db: db},
	}
}
