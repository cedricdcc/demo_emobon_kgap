# Project Roadmap

## 1. LLMs
### Specialized LLM for SPARQL Queries
- **Task 1.1**: Dataset Creation
  - Collect SPARQL query examples and corresponding results.
  - Annotate datasets for training and validation.
- **Task 1.2**: Model Configuration
  - Select a base model (e.g., Bitlas LLM).
  - Configure hyperparameters for SPARQL-specific tasks.
- **Task 1.3**: Training
  - Fine-tune the model using annotated datasets.
  - Validate performance on unseen SPARQL queries.
- **Task 1.4**: Deployment
  - Integrate the trained model into the backend.

### Delegation LLM
- **Task 2.1**: Dataset Creation
  - Collect user questions and map them to target LLMs.
- **Task 2.2**: Training
  - Fine-tune the model for accurate delegation.
- **Task 2.3**: Integration
  - Implement the delegation logic in the backend.

### Comprehension LLM
- **Task 3.1**: Dataset Creation
  - Gather triple data and corresponding UI component requirements.
- **Task 3.2**: Training
  - Train the model to analyze triples and suggest UI components.
- **Task 3.3**: Integration
  - Connect the model to the frontend for dynamic UI generation.

## 2. Backend
- **Task 4.1**: Implement Agents
  - Develop agents to handle tasks using the A2A protocol.
- **Task 4.2**: LLM Integration
  - Integrate the specialized, delegation, and comprehension LLMs.
- **Task 4.3**: Training File Management
  - Create a dedicated module for training LLMs.
  - Document training processes and configurations.

## 3. Frontend
- **Task 5.1**: Chat Application
  - Develop a chat interface for user interaction.
- **Task 5.2**: Data Visualization
  - Implement components for tabular data, graphs, and maps.
- **Task 5.3**: Data Export
  - Add functionality to download tabular data.

## 4. Research Integration
- **Task 6.1**: A2A Protocol
  - Ensure seamless communication between agents.
- **Task 6.2**: AG-UI
  - Connect the frontend to backend agents.
- **Task 6.3**: Bitlas LLM
  - Leverage Bitlas LLM for computational efficiency.
- **Task 6.4**: Training Techniques
  - Apply best practices for dataset creation and fine-tuning.

---

## UML Diagram
```mermaid
classDiagram
    %% LLMs
    class SpecializedLLM {
        +SPARQL Query Handling
    }
    class DelegationLLM {
        +Analyze User Questions
        +Delegate to LLMs
    }
    class ComprehensionLLM {
        +Analyze Triple Data
        +Delegate UI Generation
    }

    %% Backend
    class Backend {
        +Integrate LLMs
        +Train LLMs
    }
    class Agent {
        +Handle Tasks
        +A2A Protocol
    }

    %% Frontend
    class ChatApplication {
        +User Interaction
    }
    class DataDisplay {
        +Tabular Data
        +Graphs
        +Maps
    }
    class DownloadFunctionality {
        +Download Tabular Data
    }

    %% Relationships
    SpecializedLLM --> Backend : "Integrated"
    DelegationLLM --> Backend : "Integrated"
    ComprehensionLLM --> Backend : "Integrated"
    Backend --> Agent : "Uses A2A Protocol"
    Agent --> ChatApplication : "Communicates"
    Agent --> DataDisplay : "Provides Data"
    Agent --> DownloadFunctionality : "Provides Data"