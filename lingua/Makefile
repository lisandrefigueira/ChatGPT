.PHONY: dev dev-backend dev-frontend test validar deploy install

install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

dev:
	@echo "Subindo backend (http://localhost:8000) e frontend (http://localhost:5173)..."
	@trap 'kill 0' EXIT; \
	(cd backend && uvicorn main:app --reload --port 8000) & \
	(cd frontend && npm run dev) & \
	wait

dev-backend:
	cd backend && uvicorn main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

test:
	cd backend && python3 -m pytest tests/ -v
	$(MAKE) validar
	cd frontend && npm run build

validar:
	cd trilhas && python3 validar_trilhas.py

deploy:
	docker compose build
	docker compose up -d
	@echo "Deploy concluído. Verifique: curl http://localhost:8000/api/health"
