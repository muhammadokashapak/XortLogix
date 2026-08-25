# generate_aiml_interview_pdf.py
"""
Generates a comprehensive 105+ Questions & Answers Master PDF for AI & Machine Learning
Technical & Sales Engineering Interviews.
Formatted for high readability, clean typography, and seamless RAG chunk ingestion.
"""

import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

# Comprehensive 105+ AI/ML Interview Questions & Answers
AIML_SECTIONS = [
    {
        "title": "SECTION 1: Core Machine Learning & Fundamentals",
        "category": "Foundations & Classical ML",
        "qa_list": [
            {
                "q": "What is the Bias-Variance Tradeoff in Machine Learning?",
                "a": "Bias refers to the error from erroneous assumptions in the learning algorithm (underfitting). Variance refers to sensitivity to small fluctuations in training data (overfitting). The tradeoff represents the balance where total generalization error (Bias^2 + Variance + Irreducible Error) is minimized."
            },
            {
                "q": "How does L1 (Lasso) differ from L2 (Ridge) Regularization?",
                "a": "L1 adds the sum of absolute coefficients (|w|) to the loss, driving non-essential feature weights strictly to zero (producing sparse models and automatic feature selection). L2 adds the sum of squared coefficients (w^2), shrinking weights smoothly toward zero without forcing exact sparsity, stabilizing collinear features."
            },
            {
                "q": "When should you use ROC-AUC vs Precision-Recall (PR) AUC?",
                "a": "Use ROC-AUC for balanced datasets where true negatives are important. Use PR-AUC for highly imbalanced datasets (e.g. fraud detection, medical anomaly detection) because ROC-AUC gives an overly optimistic score when the negative class dominates."
            },
            {
                "q": "What is Data Leakage and how do you prevent it in ML pipelines?",
                "a": "Data leakage occurs when information from outside the training dataset (like test set distribution or future timestamps) is used to create the model. Prevent it by strict temporal splitting, fitting scalers/imputers ONLY on training folds inside cross-validation, and isolating target encoding."
            },
            {
                "q": "Explain the difference between Bagging and Boosting.",
                "a": "Bagging (e.g., Random Forest) trains multiple models independently in parallel on bootstrap samples and aggregates their predictions to reduce variance. Boosting (e.g., XGBoost, LightGBM) trains models sequentially where each new model corrects the residual errors of prior models to reduce bias."
            },
            {
                "q": "How does Gradient Boosting work under the hood?",
                "a": "Gradient Boosting builds additive trees iteratively. At each step, a new weak learner (decision tree) is fit to the negative gradient (pseudo-residuals) of the loss function with respect to current predictions, performing gradient descent in function space."
            },
            {
                "q": "What is Cross-Validation and why is K-Fold preferred over a single train/test split?",
                "a": "K-Fold splits data into K subsets, training on K-1 and testing on the remaining fold K times. It provides an unbiased estimate of model generalization across diverse data slices, reducing variance associated with a single arbitrary train/test split."
            },
            {
                "q": "What is the Curse of Dimensionality and how is it mitigated?",
                "a": "As feature dimensions grow, the volume of space increases exponentially, making data points sparse and distance metrics (Euclidean) meaningless. Mitigate via dimensionality reduction (PCA, t-SNE, UMAP), feature selection, and manifold learning."
            },
            {
                "q": "Explain Principal Component Analysis (PCA).",
                "a": "PCA is an unsupervised linear transformation technique that identifies orthogonal axes (principal components) of maximum variance in feature space by calculating the eigenvectors and eigenvalues of the data covariance matrix."
            },
            {
                "q": "How do Support Vector Machines (SVM) handle non-linear data?",
                "a": "SVM applies the 'Kernel Trick' (e.g., RBF, Polynomial kernels) to implicitly project data into a higher-dimensional space where a linear separating hyperplane with maximal margin can be constructed without computing explicit high-dimensional coordinates."
            },
            {
                "q": "What is the difference between Generative and Discriminative models in ML?",
                "a": "Discriminative models learn the boundary between classes P(Y|X) (e.g., Logistic Regression, SVM, BERT). Generative models learn the joint probability distribution P(X,Y) or P(X) to model how data was generated (e.g., Naive Bayes, GMM, GANs, GPT)."
            },
            {
                "q": "What is Target Encoding and how do you prevent target leakage?",
                "a": "Target encoding replaces categorical categories with the mean target value for that category. Prevent leakage by using Out-of-Fold (OOF) target calculation, adding Gaussian smoothing noise, and empirical Bayes prior shrinkage (m-estimate)."
            },
            {
                "q": "What is Logistic Regression and why is it called regression when it classifies?",
                "a": "Logistic Regression models the log-odds (logit) of a binary outcome as a linear combination of independent features: ln(p / (1-p)) = w^T x + b. It is a generalized linear regression model transformed into probabilities using the sigmoid function."
            },
            {
                "q": "What is the difference between Parametric and Non-Parametric algorithms?",
                "a": "Parametric models summarize data with a fixed set of parameters independent of training sample size (e.g., Linear/Logistic Regression, Neural Networks). Non-parametric models grow parameters with data complexity (e.g., KNN, Decision Trees, SVM with RBF)."
            },
            {
                "q": "How do you handle severe Class Imbalance in classification?",
                "a": "Techniques include: (1) Cost-sensitive loss weighting (Focal Loss, Class Weights), (2) Resampling (SMOTE oversampling minority, Tomek Links undersampling majority), (3) Threshold calibration / moving, and (4) Anomaly detection formulation (Isolation Forests)."
            },
            {
                "q": "Explain the difference between Type I and Type II errors.",
                "a": "Type I error is a False Positive (rejecting a true null hypothesis, e.g., innocent person convicted). Type II error is a False Negative (failing to reject a false null hypothesis, e.g., failing to detect a critical disease)."
            },
            {
                "q": "How does K-Means Clustering work and what is its main limitation?",
                "a": "K-Means iteratively assigns points to the nearest cluster centroid (Voronoi partition) and recalculates centroids as the mean of assigned points. Limitations: Assumes spherical clusters of equal size, sensitive to initialization (mitigated by K-Means++), and requires pre-specifying K."
            },
            {
                "q": "What is the Elbow Method and Silhouette Score in Clustering?",
                "a": "Elbow method plots Within-Cluster Sum of Squares (WCSS) vs K to locate diminishing returns. Silhouette Score measures how similar an object is to its own cluster compared to neighboring clusters (-1 to +1, higher is better)."
            },
            {
                "q": "What is Early Stopping and why is it a form of regularization?",
                "a": "Early stopping monitors validation loss during training and halts optimization when validation loss stops decreasing for N epochs (patience). It restricts parameter magnitude growth, effectively constraining model capacity similar to L2 weight decay."
            },
            {
                "q": "What is Confusion Matrix and its four core derived metrics?",
                "a": "The confusion matrix tallies TP, FP, TN, FN. Core metrics: Accuracy = (TP+TN)/Total, Precision = TP/(TP+FP), Recall/Sensitivity = TP/(TP+FN), and F1-Score = 2 * (Precision * Recall) / (Precision + Recall)."
            }
        ]
    },
    {
        "title": "SECTION 2: Deep Learning & Neural Network Architecture",
        "category": "Deep Learning & Neural Networks",
        "qa_list": [
            {
                "q": "Explain Backpropagation and the Chain Rule in Neural Networks.",
                "a": "Backpropagation computes the gradient of the loss function with respect to all network weights by repeatedly applying the multivariable calculus chain rule backward from the output layer to the input layer, enabling gradient descent weight updates."
            },
            {
                "q": "What causes Vanishing and Exploding Gradients and how are they resolved?",
                "a": "Repeated matrix multiplications of gradients < 1 (vanishing) or > 1 (exploding) across deep layers. Solved via: (1) Residual Connections (ResNet), (2) ReLU/GELU activations instead of Sigmoid/Tanh, (3) Batch/Layer Normalization, (4) He/Xavier weight initialization, and (5) Gradient Clipping."
            },
            {
                "q": "How does the Adam optimizer improve over Stochastic Gradient Descent (SGD)?",
                "a": "Adam computes adaptive learning rates for each parameter by combining Momentum (first moment: moving average of gradients) and RMSProp (second moment: moving average of squared gradients) with bias correction."
            },
            {
                "q": "What is the difference between Batch Normalization and Layer Normalization?",
                "a": "Batch Normalization normalizes activations across the batch dimension for each feature channel (effective in CNNs). Layer Normalization normalizes across all features/hidden dimensions for each individual sequence element independently of batch size (essential in Transformers and RNNs)."
            },
            {
                "q": "Why is GELU preferred over ReLU in modern Transformer LLMs?",
                "a": "GELU (Gaussian Error Linear Unit) scales inputs by their cumulative probability distribution under standard normal distribution, providing a smooth non-monotonic curvature around zero that avoids the 'dying ReLU' zero-derivative dead state."
            },
            {
                "q": "What is Dropout and how does it behave during training vs inference?",
                "a": "Dropout randomly sets a fraction p of neuron activations to zero during training to prevent co-adaptation of features (acting as an implicit ensemble). During inference, dropout is disabled and activations are scaled by (1-p) or left as-is if inverted dropout was used."
            },
            {
                "q": "Explain Convolutional Neural Networks (CNNs) and Translation Invariance.",
                "a": "CNNs apply learnable spatial filters (kernels) that slide across inputs via parameter sharing and local receptive fields. Pooling and shared weights provide translation invariance, enabling detection of patterns regardless of their coordinate position."
            },
            {
                "q": "What is the key advantage of ResNet's Skip/Residual Connections?",
                "a": "Skip connections reformulate layers to learn residual mappings F(x) = H(x) - x, where output is F(x) + x. This allows gradients to flow directly through the identity shortcut during backpropagation, enabling stable training of 100+ layer networks."
            },
            {
                "q": "How do LSTMs solve the short-term memory problem of standard RNNs?",
                "a": "LSTMs introduce a continuous Cell State regulated by three gates: Forget Gate (discards irrelevant past info), Input Gate (writes new candidate info), and Output Gate (filters cell state into the hidden state output)."
            },
            {
                "q": "What is the Self-Attention mechanism in Transformers?",
                "a": "Self-attention maps input tokens into Query (Q), Key (K), and Value (V) matrices. It computes Attention(Q,K,V) = softmax(Q * K^T / sqrt(d_k)) * V, enabling every token in a sequence to dynamically attend to every other token with O(1) path length."
            },
            {
                "q": "Why is the scaling factor 1/sqrt(d_k) used in Scaled Dot-Product Attention?",
                "a": "For large projection dimensions d_k, dot products grow large in magnitude, pushing softmax into regions with extremely small gradients. Dividing by sqrt(d_k) normalizes the variance to 1, maintaining healthy gradient propagation."
            },
            {
                "q": "What is Multi-Head Attention and why is it better than Single-Head Attention?",
                "a": "Multi-Head Attention projects Q, K, V into h distinct lower-dimensional subspaces in parallel. This allows the model to jointly attend to information from different representation subspaces (e.g., grammatical syntax, semantic coreference, factual relations)."
            },
            {
                "q": "Explain Positional Embeddings and RoPE (Rotary Position Embeddings).",
                "a": "Because self-attention is permutation-invariant, positional encodings inject sequence order. RoPE applies a rotation matrix to Query and Key vectors in complex coordinate space, naturally incorporating relative token distances while generalizing to long contexts."
            },
            {
                "q": "What is the difference between Encoder-Only, Decoder-Only, and Encoder-Decoder architectures?",
                "a": "Encoder-Only (BERT) uses bidirectional attention for representation and classification. Decoder-Only (GPT, Llama) uses causal/masked self-attention for autoregressive token generation. Encoder-Decoder (T5) maps input sequences to target sequences (translation, summarization)."
            },
            {
                "q": "What is Cross-Entropy Loss and why is it standard for classification?",
                "a": "Cross-Entropy Loss H(p,q) = -sum(p(x) * log(q(x))) measures the divergence between true label distribution p and predicted softmax probability q. Minimizing cross-entropy is equivalent to maximizing the log-likelihood of the correct class."
            },
            {
                "q": "What is Learning Rate Warmup and Cosine Annealing?",
                "a": "Warmup gradually increases learning rate from zero during initial steps to stabilize variance calculations (Adam). Cosine annealing then smoothly decays the learning rate following a cosine curve to zero, allowing the optimizer to settle into flatter minima."
            },
            {
                "q": "What is Weight Initialization (He vs Xavier) and why is it critical?",
                "a": "Xavier/Glorot initializes weights with variance 2/(n_in + n_out) for Tanh/Sigmoid. He/Kaiming initializes with variance 2/n_in for ReLU/GELU to keep signal variance constant across layers and prevent activation collapse."
            },
            {
                "q": "Explain Teacher Forcing in Sequence-to-Sequence models.",
                "a": "Teacher forcing passes the ground-truth target token from the training dataset as the next input step instead of feeding the model's own prior predicted token, accelerating convergence during training."
            }
        ]
    },
    {
        "title": "SECTION 3: Large Language Models (LLMs) & Generative AI",
        "category": "LLMs & Generative AI",
        "qa_list": [
            {
                "q": "What is LoRA (Low-Rank Adaptation) and how does it work?",
                "a": "LoRA freezes pre-trained weight matrices W_0 (d x k) and injects trainable rank decomposition matrices A (d x r) and B (r x k) where r << min(d,k). The updated forward pass is W = W_0 + (alpha/r) * (B * A), reducing trainable parameters by 99%."
            },
            {
                "q": "What is QLoRA and how does it achieve 4-bit fine-tuning without quality degradation?",
                "a": "QLoRA combines: (1) NF4 (NormalFloat4) information-theoretically optimal 4-bit quantization, (2) Double Quantization to compress quantization constants, and (3) Paged Optimizers to manage memory spikes during gradient checkpoints."
            },
            {
                "q": "Explain the difference between RLHF and DPO (Direct Preference Optimization).",
                "a": "RLHF trains a separate Reward Model on human preferences and optimizes policy via PPO (complex and unstable). DPO mathematically re-parameterizes the reward in terms of policy probabilities, optimizing preference directly via cross-entropy loss without a separate reward model or RL loop."
            },
            {
                "q": "What are Temperature, Top-P (Nucleus Sampling), and Top-K in LLM generation?",
                "a": "Temperature divides logits (lower = deterministic/focused, higher = creative/diverse). Top-K restricts sampling to the K highest probability tokens. Top-P restricts sampling to the smallest set of tokens whose cumulative probability exceeds threshold P."
            },
            {
                "q": "How does KV Caching optimize Transformer autoregressive inference?",
                "a": "During token generation, past Keys and Values do not change. KV Cache stores previous Keys and Values in GPU VRAM, converting token generation complexity from O(N^2) to O(N) per step by computing attention only for the newest token against cached states."
            },
            {
                "q": "What is FlashAttention and why is it faster?",
                "a": "FlashAttention tiles the Query, Key, Value matrices to fit entirely into fast GPU SRAM and computes softmax on-chip using online softmax normalization, avoiding high-latency reads/writes to slower GPU HBM memory."
            },
            {
                "q": "What causes LLM Hallucinations and how are they engineered out?",
                "a": "Hallucinations stem from statistical pattern completion over knowledge cutoff, lossy pre-training compression, and misalignment. Solved via: (1) Grounded RAG retrieval, (2) System Guardrails (NeMo, Llama Guard), (3) Structured JSON schema enforcement, and (4) Chain-of-Thought citation verification."
            },
            {
                "q": "What is Instruction Tuning vs Pre-training vs Alignment?",
                "a": "Pre-training learns language syntax and world knowledge via next-token prediction on trillions of tokens. Instruction Tuning (SFT) teaches the model to respond to conversational commands. Alignment (RLHF/DPO) ensures outputs are helpful, honest, and harmless."
            },
            {
                "q": "Explain Tokenization (Byte-Pair Encoding - BPE).",
                "a": "BPE starts with character-level vocabulary and iteratively merges the most frequently co-occurring pair of symbols into new tokens until target vocabulary size is reached, balancing vocabulary size with sequence compression."
            },
            {
                "q": "What is Mixture of Experts (MoE) architecture (e.g. Mixtral)?",
                "a": "MoE replaces standard dense feedforward layers with multiple sparse 'expert' networks. A learnable routing/gating mechanism dynamically activates only top-K (e.g., 2 of 8) experts per token, delivering large-model parameter capacity at fraction of compute cost."
            },
            {
                "q": "How does Speculative Decoding accelerate LLM generation?",
                "a": "A smaller, fast draft model generates K candidate tokens in parallel, which are then verified in a single forward pass by the large target model. Correct tokens are accepted while the first incorrect token is resampled, achieving 2-3x speedup with identical output distribution."
            },
            {
                "q": "What is Chain-of-Thought (CoT) prompting and why does it improve reasoning?",
                "a": "CoT prompts the model to generate intermediate reasoning steps ('Think step-by-step') before giving the final answer. This allocates extra computation tokens to complex multi-step logical deductions."
            },
            {
                "q": "Explain Model Quantization (GPTQ, AWQ, GGUF).",
                "a": "Quantization converts 16-bit FP weights to 8-bit or 4-bit INT. GPTQ uses second-order Taylor expansion for post-training quantization. AWQ protects salient 1% outlier weights. GGUF provides unified CPU/GPU quantized tensor formatting."
            },
            {
                "q": "What are LLM Context Extension techniques (YARN, LongLoRA, Sliding Window)?",
                "a": "Sliding window attention limits attention to local neighbors. LongLoRA uses shifted short-attention for fine-tuning. YaRN (Yet another RoPE extensioN) interpolates position frequencies across hidden dimensions to scale context up to 128k+ tokens."
            },
            {
                "q": "What is the difference between Function Calling and Tool Use in LLMs?",
                "a": "Function calling outputs structured JSON parameters matching a predefined schema. Tool use executes that function against external APIs/databases and returns execution results back into LLM context to complete the task."
            }
        ]
    },
    {
        "title": "SECTION 4: RAG (Retrieval-Augmented Generation) & Vector Search",
        "category": "RAG & Vector Search",
        "qa_list": [
            {
                "q": "Explain the core RAG (Retrieval-Augmented Generation) pipeline architecture.",
                "a": "Pipeline: (1) Ingestion: Documents are parsed, chunked, and embedded into a Vector DB. (2) Retrieval: User query is converted to embedding and cosine similarity matches top-K chunks. (3) Augmentation: Retrieved chunks are injected into LLM prompt context. (4) Generation: LLM synthesizes grounded answer with citations."
            },
            {
                "q": "What is the difference between Dense Retrieval and Sparse Retrieval (BM25)?",
                "a": "Dense retrieval (embeddings) captures semantic context and synonyms but can miss exact product codes or names. Sparse retrieval (BM25 / TF-IDF) matches exact keywords and lexical frequency. Hybrid search combines both via Reciprocal Rank Fusion (RRF)."
            },
            {
                "q": "What is HNSW (Hierarchical Navigable Small World) indexing in Vector DBs?",
                "a": "HNSW is an Approximate Nearest Neighbor (ANN) search graph with multi-layer hierarchies. Top layers have long-range links for fast greedy routing, while bottom layers contain dense local connections for accurate nearest-neighbor discovery with O(log N) search latency."
            },
            {
                "q": "Explain Reciprocal Rank Fusion (RRF) in Hybrid Search.",
                "a": "RRF combines rankings from multiple retrieval algorithms (dense vector + sparse BM25) using score formula: RRF_Score(d) = sum(1 / (k + rank_i(d))), where k is a smoothing constant (typically 60), ensuring balanced reranking without score normalization artifacts."
            },
            {
                "q": "What is Re-ranking (Cross-Encoder) and why is it applied after Bi-Encoder retrieval?",
                "a": "Bi-encoders independently embed query and document (fast, scalable for million-item search). Cross-encoders process query and candidate chunk jointly through full cross-attention layers, computing precise relevance scores on the top-50 candidates to boost precision."
            },
            {
                "q": "What chunking strategies are used in production RAG systems?",
                "a": "Strategies: (1) Fixed-size sliding window with overlap (e.g. 512 tokens, 50 overlap), (2) Markdown/HTML semantic structure chunking, (3) Document-specific Q&A card splitting, (4) Parent-Document retrieval (embed small sentences, return full parent paragraph)."
            },
            {
                "q": "What is the 'Lost in the Middle' problem in LLM context and how is it mitigated?",
                "a": "LLMs attend heavily to information at the very beginning and end of long context windows, ignoring details placed in the middle. Solved via re-ranking most critical chunks to the extreme prompt start/end, and chunk filtering."
            },
            {
                "q": "Explain Multi-Hop RAG and Agentic Query Decomposition.",
                "a": "When a query requires synthesizing multiple disjoint facts ('Compare revenue of X in 2024 with Y in 2023'), the agent decomposes the query into sub-queries, executes sequential retrievals, and aggregates results iteratively."
            },
            {
                "q": "What metrics evaluate RAG performance (Ragas framework)?",
                "a": "Core RAG metrics: (1) Faithfulness (grounded in context, no hallucination), (2) Answer Relevance (answers the user's prompt), (3) Context Precision (retrieved chunks signal-to-noise ratio), and (4) Context Recall (retrieved all necessary facts)."
            },
            {
                "q": "How does Hypothetical Document Embeddings (HyDE) improve retrieval?",
                "a": "HyDE prompts an LLM to generate a hypothetical answer to the user query. The hypothetical answer is embedded and used to search the vector database, matching real document embeddings closer in embedding space than raw short questions."
            },
            {
                "q": "What is Vector Embedding Dimensionality and Cosine vs Dot Product vs L2 Distance?",
                "a": "Dimensionality is the vector size (e.g., 384, 768, 1536). If embeddings are L2-normalized (length=1), Cosine Similarity, Dot Product, and Euclidean (L2) Distance are monotonically equivalent, but Dot Product is computationally fastest."
            },
            {
                "q": "How do you handle Multi-Tenancy and Data Isolation in Vector Databases?",
                "a": "Approaches: (1) Metadata filtering (querying with `where user_id = X` filter), (2) Dedicated isolated collections/indexes per tenant, and (3) Cryptographic encryption per user namespace in partitioned storage."
            },
            {
                "q": "What is Contextual Compression in RAG?",
                "a": "Contextual compression extracts only the relevant sentences or entities from retrieved candidate documents relative to the query before sending them to the LLM, reducing latency, token cost, and distraction."
            },
            {
                "q": "Explain Self-RAG and Adaptive Retrieval.",
                "a": "Self-RAG trains the model to generate reflection tokens that decide whether retrieval is necessary on-demand, evaluate whether retrieved passages are relevant, and self-critique generation quality before streaming output."
            }
        ]
    },
    {
        "title": "SECTION 5: MLOps, System Design & Inference Serving",
        "category": "MLOps & System Design",
        "qa_list": [
            {
                "q": "How does vLLM and PagedAttention achieve 10x higher LLM serving throughput?",
                "a": "PagedAttention manages KV Cache memory fragmentation by allocating KV blocks non-contiguously in virtual memory pages (like OS virtual paging), virtually eliminating VRAM waste and enabling continuous dynamic batching of concurrent user requests."
            },
            {
                "q": "What is Continuous Batching (Iteration-level batching) in LLM serving?",
                "a": "Traditional batching waits for all sequences in a batch to finish generation. Continuous batching evicts completed requests immediately at each iteration token step and injects incoming requests into the active batch without waiting."
            },
            {
                "q": "What is Model Drift (Concept Drift vs Data Drift) and how is it detected?",
                "a": "Data Drift: Distribution of input features P(X) changes over time (detected via Kolmogorov-Smirnov test, PSI - Population Stability Index). Concept Drift: Relationship between features and target P(Y|X) changes (detected via ground-truth performance degradation monitoring)."
            },
            {
                "q": "Explain Latency vs Throughput tradeoffs in Machine Learning systems.",
                "a": "Latency (TTFT - Time to First Token, P99 response time) is critical for real-time user-facing applications (requires smaller batch sizes and model parallelism). Throughput (tokens/sec) maximizes hardware efficiency for batch offline processing (requires continuous large batching)."
            },
            {
                "q": "What is Tensor Parallelism vs Pipeline Parallelism in distributed training/inference?",
                "a": "Tensor Parallelism splits individual weight matrices across GPUs within the same server (Megatron-LM, intra-node high-bandwidth NVLink). Pipeline Parallelism splits layers across different GPUs sequentially (inter-node)."
            },
            {
                "q": "How do you secure LLM applications against Prompt Injection attacks?",
                "a": "Techniques: (1) Strict prompt/system role separation, (2) Input sanitization and dual-LLM guardrail verification, (3) Parameterized structured tools (function calling) instead of raw text shell execution, and (4) Principle of least privilege for database integrations."
            },
            {
                "q": "What is Feature Store (e.g. Feast, Hopsworks) and why is it used?",
                "a": "A Feature Store provides a centralized repository for standardized feature definitions, serving low-latency online features for real-time inference (Redis) and point-in-time correct offline features for model training, preventing training-serving skew."
            },
            {
                "q": "Explain ONNX (Open Neural Network Exchange) and TensorRT runtime optimization.",
                "a": "ONNX provides an open graph format interoperable across frameworks (PyTorch, TensorFlow). TensorRT optimizes ONNX graphs for NVIDIA GPUs through layer fusion, kernel auto-tuning, and precision quantization (FP16/INT8)."
            },
            {
                "q": "What is Canary Deployment vs Shadow Deployment in ML model rollout?",
                "a": "Canary routes a small percentage of live user traffic (e.g., 5%) to the new model while monitoring error rates. Shadow deployment mirrors 100% of live traffic to the new model without serving its outputs to users, validating performance safely against live load."
            },
            {
                "q": "What is Data Lineage and Model Reproducibility in MLOps?",
                "a": "Data Lineage tracks the complete provenance, transformations, and dependencies of training data (DVC). Model Reproducibility guarantees identical model artifact regeneration using tracked git commits, pinned seed parameters, and containerized Docker environments."
            }
        ]
    },
    {
        "title": "SECTION 6: AI Sales Engineering, Strategy & Client Pitching",
        "category": "Sales & Enterprise AI Strategy",
        "qa_list": [
            {
                "q": "How do you address client concerns about Data Privacy when using AI solutions?",
                "a": "Explain that: (1) Architecture runs completely local or within dedicated private VPCs (zero external data sharing), (2) Enterprise Zero-Data-Retention (ZDR) agreements apply, (3) Client data is never used for foundation model training, and (4) Role-Based Access Control (RBAC) ensures cryptographic isolation."
            },
            {
                "q": "Open-Source Local Models (Llama 3, Mistral) vs Proprietary APIs (OpenAI, Anthropic) - What is the sales pitch?",
                "a": "Proprietary APIs offer fast prototyping but incur continuous per-token operational expenses and privacy risks. Open-source local deployments give 100% data sovereignty, zero recurring API usage bills, predictable fixed infrastructure costs, and customized fine-tuning ownership."
            },
            {
                "q": "How do you handle client objection: 'Why shouldn't we just build this in-house?'",
                "a": "In-house builds require 6-9 months of senior AI engineering salaries ($300k+), expensive GPU trial-and-error, and continuous infrastructure maintenance. We provide a battle-tested, production-grade co-pilot platform deployed in 7 days at a fraction of the cost with guaranteed SLA."
            },
            {
                "q": "How do you guarantee Low Latency for real-time sales / voice co-pilot apps?",
                "a": "We utilize localized WASAPI audio loopback streaming, quantized fast embedding models (all-MiniLM-L6-v2), in-memory ChromaDB vector indexing with <15ms retrieval, and instant WebSocket push to achieve sub-second real-time battlecard matching."
            },
            {
                "q": "What is Total Cost of Ownership (TCO) calculation for an Enterprise AI Agent?",
                "a": "TCO includes: (1) Compute / GPU hosting (cloud vs on-prem), (2) Vector storage and maintenance, (3) Data ingestion pipelines, and (4) Engineering support. We optimize TCO through local 4-bit quantization, dynamic scaling, and reusable RAG indexing."
            },
            {
                "q": "How do you pitch AI ROI to a non-technical C-level Executive?",
                "a": "Focus strictly on business impact metrics: (1) 40% reduction in sales onboarding ramp time, (2) 3x faster objection handling during live customer pitches, (3) 25% higher deal conversion rates, and (4) Automated compliance audit trails."
            },
            {
                "q": "How do you assure clients about AI Accuracy and Hallucination Prevention?",
                "a": "Our system implements Strict Grounded RAG with exact similarity threshold gating. If similarity falls below 75%, the system suppresses generic AI outputs and cites only verified company sales playbooks, ensuring 100% factual fidelity."
            },
            {
                "q": "What is our Disaster Recovery & Backup Strategy for Enterprise AI Data?",
                "a": "All custom strategy playbooks, user embeddings, and chat logs are backed up in parallel to Google Drive API v3 and SQLite persistent volumes with automated daily snapshots and 1-click restore capabilities."
            }
        ]
    },
    {
        "title": "SECTION 7: AI Agents, Workflows & Tool Execution",
        "category": "Agentic AI & Orchestration",
        "qa_list": [
            {
                "q": "Explain the ReAct (Reasoning + Acting) Agent framework.",
                "a": "ReAct interleaves reasoning traces ('Thought') and task-specific actions ('Action': tool call) in an iterative loop. The agent observes tool execution results ('Observation') and reasons about the next step until the final answer is achieved."
            },
            {
                "q": "What is the difference between Graph-based (LangGraph) vs Linear Agent workflows?",
                "a": "Linear chains execute step-by-step without cycles. Graph-based workflows represent agent states as nodes and conditional transitions as edges, enabling cyclical loops, human-in-the-loop approvals, branching decisions, and persistent memory."
            },
            {
                "q": "How do AI Agents maintain Long-Term Memory (Episodic vs Semantic)?",
                "a": "Semantic memory stores facts and world knowledge in vector databases. Episodic memory stores specific past conversation trajectories and execution outcomes, retrieved via recency, relevance, and importance scoring."
            },
            {
                "q": "What is Plan-and-Solve Prompting vs Tree-of-Thoughts (ToT)?",
                "a": "Plan-and-Solve decomposes complex tasks into an explicit checklist of subtasks before execution. Tree-of-Thoughts explores multiple reasoning paths simultaneously as a tree, using search algorithms (BFS/DFS) with self-evaluation heuristics."
            },
            {
                "q": "What is Reflection and Self-Correction in Multi-Agent systems?",
                "a": "A secondary critic/evaluator agent inspects the output of the generator agent against requirements, unit tests, or lint checks, providing structured feedback that the generator agent uses to iteratively refine its output."
            },
            {
                "q": "How do you prevent infinite loops in Autonomous Agent execution?",
                "a": "Enforce: (1) Hard maximum iteration caps (e.g., max 10 steps), (2) Token budget ceiling, (3) Duplicate action detection, (4) Timeout watchdogs, and (5) Graceful fallback escalation to human operators."
            },
            {
                "q": "What is MCP (Model Context Protocol) by Anthropic?",
                "a": "MCP is an open standard protocol that connects AI models to external data sources, enterprise tools, and local development environments through a standardized client-server architecture, replacing bespoke one-off API integrations."
            },
            {
                "q": "Explain Multi-Agent Collaboration architectures (Supervisor vs Swarm vs Hierarchical).",
                "a": "Supervisor routes tasks to specialist sub-agents. Swarm allows decentralized peer-to-peer handoffs. Hierarchical organizes agents into multi-level managers that delegate sub-goals and synthesize reports."
            },
            {
                "q": "How do you test and benchmark AI Agents in production?",
                "a": "Using deterministic evaluation harnesses (e.g. SWE-bench, GAIA) with mocked sandbox environments, trajectory verification, tool call schema validation, and end-state goal achievement assertions."
            },
            {
                "q": "What are Guardrails in AI Agent execution?",
                "a": "Input/output filters that enforce strict safety boundaries: (1) PII redacting, (2) Hallucination verification against source docs, (3) SQL injection / toxic code blocking, and (4) Structured JSON schema validation."
            }
        ]
    },
    {
        "title": "SECTION 8: Computer Vision & Multimodal AI",
        "category": "Vision & Multimodal",
        "qa_list": [
            {
                "q": "Explain CLIP (Contrastive Language-Image Pretraining) and Contrastive Loss.",
                "a": "CLIP trains an image encoder and text encoder jointly on 400M (image, text) pairs. It maximizes the cosine similarity of true pairs (diagonal) while minimizing similarity of incorrect pairs (off-diagonal) using symmetric cross-entropy infoNCE loss."
            },
            {
                "q": "How does Vision Transformer (ViT) process images without convolutions?",
                "a": "ViT flattens an image into non-overlapping 16x16 pixel patches, linearly projects each patch into 1D token embeddings, adds 1D learnable position embeddings, prepends a [CLS] token, and feeds them through standard Transformer encoder blocks."
            },
            {
                "q": "What is Diffusion Model (DDPM) and how does it generate images?",
                "a": "Forward process gradually adds Gaussian noise to an image over T steps until it becomes pure noise. Reverse process trains a U-Net to predict and subtract the added noise step-by-step, transforming pure Gaussian noise into realistic images."
            },
            {
                "q": "What is Latent Diffusion (Stable Diffusion) and why is it faster than pixel diffusion?",
                "a": "Latent Diffusion uses a pre-trained VQ-VAE / Autoencoder to compress high-resolution images into a lower-dimensional latent space (e.g., 8x spatial reduction). Diffusion denoising is performed entirely in latent space, slashing compute requirements."
            },
            {
                "q": "What is Object Detection: Two-Stage (Faster R-CNN) vs One-Stage (YOLO)?",
                "a": "Two-stage models (Faster R-CNN) first generate candidate regions (RPN) and then classify/refine bounding boxes (higher accuracy, slower). One-stage models (YOLO) treat detection as a single regression problem across spatial grid cells (faster, real-time)."
            },
            {
                "q": "What is Intersection over Union (IoU) and Non-Maximum Suppression (NMS)?",
                "a": "IoU = Area of Overlap / Area of Union between predicted and ground-truth boxes. NMS eliminates redundant overlapping bounding boxes for the same object by sorting by confidence and discarding boxes with IoU > threshold with the top box."
            },
            {
                "q": "How do Multimodal LLMs (GPT-4V, LLaVA) process images alongside text?",
                "a": "A vision encoder (CLIP ViT) extracts image feature tokens. A linear projection layer or Q-Former aligns visual feature dimensions with the LLM's text token embedding space, allowing visual tokens to be prepended directly into the LLM context."
            },
            {
                "q": "What is Semantic Segmentation vs Instance Segmentation vs Panoptic Segmentation?",
                "a": "Semantic: Labels every pixel by class without distinguishing instances (all cars are one color). Instance: Identifies and segments individual objects of distinct instances. Panoptic: Combines semantic and instance segmentation (stuff + things)."
            }
        ]
    },
    {
        "title": "SECTION 9: Reinforcement Learning, Benchmarks & AI Hardware",
        "category": "RL, Evaluation & Hardware",
        "qa_list": [
            {
                "q": "What is Markov Decision Process (MDP) and the Bellman Equation?",
                "a": "An MDP is defined by (States S, Actions A, Transition Probabilities P, Rewards R, Discount Factor gamma). The Bellman Equation expresses value V(s) recursively as the immediate reward plus discounted expected value of successor states: V(s) = max_a [ R(s,a) + gamma * sum( P(s'|s,a) * V(s') ) ]."
            },
            {
                "q": "What is the difference between Q-Learning and Policy Gradient methods?",
                "a": "Q-Learning is value-based (learns optimal action-value Q(s,a) and derives policy via argmax Q). Policy Gradients (REINFORCE, PPO) parameterize policy pi(a|s) directly and optimize expected reward via gradient ascent, handling continuous action spaces."
            },
            {
                "q": "Explain PPO (Proximal Policy Optimization) and Clipped Surrogate Objective.",
                "a": "PPO stabilizes policy gradient training by clipping the probability ratio r_t(theta) = pi_theta(a|s) / pi_old(a|s) within [1-epsilon, 1+epsilon], preventing destructively large policy updates in a single training step."
            },
            {
                "q": "What are the standard LLM Evaluation Benchmarks (MMLU, GSM8K, HumanEval)?",
                "a": "MMLU: 57-subject multidisciplinary factual knowledge. GSM8K: Grade-school multi-step mathematical reasoning. HumanEval: Python programming problem solving. MT-Bench / LMSYS Chatbot Arena: Conversational quality and human preference Elo."
            },
            {
                "q": "What is Memory Bandwidth Bottleneck (Memory-bound vs Compute-bound) in LLM Inference?",
                "a": "Autoregressive token generation loads gigabytes of weights from GPU HBM memory for every single token forward pass, making inference memory-bandwidth bound rather than compute (TFLOPS) bound. Techniques like quantization and continuous batching alleviate this."
            },
            {
                "q": "What is the difference between NVIDIA Tensor Cores, FP8 precision, and Groq LPU?",
                "a": "Tensor Cores perform mixed-precision matrix multiply-accumulate (MMA) in hardware. FP8 halves memory footprint and doubles compute throughput over FP16. Groq LPU (Language Processing Unit) uses deterministic SRAM architecture without external DRAM latency."
            },
            {
                "q": "What is Data Parallelism (DDP) vs ZeRO (Zero Redundancy Optimizer)?",
                "a": "DDP replicates model weights, gradients, and optimizer states across all GPUs. ZeRO partitions optimizer states (ZeRO-1), gradients (ZeRO-2), and model parameters (ZeRO-3) across GPUs, eliminating memory redundancy and enabling training of trillion-parameter models."
            }
        ]
    }
]

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#0284c7"))
        
        # Header (Pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 755, "XORTLOGIX AI / ML MASTER INTERVIEW BIBLE — 105+ Q&A")
            self.drawRightString(558, 755, "CONFIDENTIAL & PROPRIETARY")
            self.setStrokeColor(colors.HexColor("#e2e8f0"))
            self.setLineWidth(0.75)
            self.line(54, 748, 558, 748)

        # Footer
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        self.drawString(54, 35, "Generated for Sales Co-Pilot & AI Engineering Interviews | XortLogix Technologies")
        self.drawRightString(558, 35, f"Page {self._pageNumber} of {page_count}")
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.75)
        self.line(54, 46, 558, 46)
        
        self.restoreState()

def generate_pdf(output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom Clean Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#0284c7'),
        spaceAfter=14
    )

    section_header_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#ffffff'),
        spaceAfter=0
    )

    q_style = ParagraphStyle(
        'QuestionStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=3
    )

    a_style = ParagraphStyle(
        'AnswerStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12.5,
        textColor=colors.HexColor('#334155'),
        spaceAfter=0
    )

    meta_style = ParagraphStyle(
        'MetaStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#64748b')
    )

    story = []

    # Title Banner Block
    story.append(Paragraph("AI & MACHINE LEARNING INTERVIEW MASTER BIBLE", title_style))
    story.append(Paragraph("105+ Technical, System Design, RAG, LLM & Sales Engineering Questions & Answers", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0284c7'), spaceAfter=14))

    # Meta Overview Box
    meta_html = (
        "<b>Publisher:</b> XortLogix AI Co-Pilot Knowledge Base &nbsp;|&nbsp; "
        "<b>Target Roles:</b> AI/ML Engineer, Data Scientist, AI Sales Architect &nbsp;|&nbsp; "
        "<b>Total Q&As:</b> 105 Questions"
    )
    meta_table = Table(
        [[Paragraph(meta_html, meta_style)]],
        colWidths=[504]
    )
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f1f5f9')),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
        ('ROUNDEDCORNERS', [4, 4, 4, 4]),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 14))

    global_q_num = 1

    for section in AIML_SECTIONS:
        # Section Header Banner
        sec_header_table = Table(
            [[Paragraph(f"<b>{section['title']}</b>", section_header_style)]],
            colWidths=[504]
        )
        sec_header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#0f172a')),
            ('PADDING', (0, 0), (-1, -1), 7),
            ('TOPPADDING', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ]))
        story.append(Spacer(1, 8))
        story.append(sec_header_table)
        story.append(Spacer(1, 8))

        for qa in section["qa_list"]:
            q_text = f"Q{global_q_num}. {qa['q']}"
            a_text = f"<b>Context / Answer:</b> {qa['a']}"

            card_content = [
                [Paragraph(f"<b>{q_text}</b>", q_style)],
                [Paragraph(a_text, a_style)]
            ]

            card_table = Table(card_content, colWidths=[504])
            card_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ffffff')),
                ('LINELEFT', (0, 0), (0, -1), 3, colors.HexColor('#0284c7')),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ]))

            story.append(card_table)
            story.append(Spacer(1, 5))
            global_q_num += 1

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"✅ Generated Master Interview PDF with {global_q_num - 1} questions at: {output_path}")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    out_file = os.path.join(base_dir, "AI_ML_Interview_Master_100_Questions.pdf")
    generate_pdf(out_file)
