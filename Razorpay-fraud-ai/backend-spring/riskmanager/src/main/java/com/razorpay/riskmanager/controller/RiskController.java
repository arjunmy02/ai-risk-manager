package com.razorpay.riskmanager.controller;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestClient;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = {
        "http://localhost:5500",
        "http://127.0.0.1:5500"
})
public class RiskController {

    private final RestClient restClient;

    public RiskController(RestClient.Builder builder) {

        this.restClient = builder
                .baseUrl("http://127.0.0.1:8000")
                .build();
    }


    // =========================================
    // BACKEND HEALTH
    // =========================================

    @GetMapping("/health")
    public Map<String, String> health() {

        Map<String, String> response = new HashMap<>();

        response.put("status", "healthy");
        response.put("backend", "Spring Boot");
        response.put("ml_service", "FastAPI");

        return response;
    }


    // =========================================
    // FRAUD PREDICTION
    // =========================================

    @PostMapping("/predict")
    public ResponseEntity<?> predict(
            @RequestBody Map<String, Object> transaction) {

        System.out.println(
                "➡️ Spring Boot received prediction request"
        );

        try {

            Map<String, Object> result =
                    restClient
                            .post()
                            .uri("/predict")
                            .body(transaction)
                            .retrieve()
                            .body(Map.class);


            System.out.println(
                    "✅ FastAPI response received"
            );

            return ResponseEntity.ok(result);

        } catch (Exception e) {

            System.err.println(
                    "❌ ML service unavailable: "
                            + e.getMessage()
            );


            Map<String, Object> error =
                    new HashMap<>();

            error.put(
                    "status",
                    "error"
            );

            error.put(
                    "message",
                    "Risk analysis service is temporarily unavailable."
            );

            error.put(
                    "action",
                    "REVIEW"
            );


            return ResponseEntity
                    .status(HttpStatus.SERVICE_UNAVAILABLE)
                    .body(error);
        }
    }
}