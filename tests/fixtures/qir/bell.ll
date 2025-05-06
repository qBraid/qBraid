; ModuleID = 'LLVMDialectModule'
source_filename = "LLVMDialectModule"

%Qubit = type opaque
%Result = type opaque

@cstr.72303030303000 = private constant [7 x i8] c"r00000\00"
@cstr.72303030303100 = private constant [7 x i8] c"r00001\00"

define void @__nvqpp__mlirgen____nvqppBuilderKernel_JIG28W9O6V() local_unnamed_addr #0 {
  tail call void @__quantum__qis__h__body(%Qubit* null)
  tail call void @__quantum__qis__cnot__body(%Qubit* null, %Qubit* nonnull inttoptr (i64 1 to %Qubit*))
  tail call void @__quantum__qis__mz__body(%Qubit* null, %Result* null)
  tail call void @__quantum__qis__mz__body(%Qubit* nonnull inttoptr (i64 1 to %Qubit*), %Result* nonnull inttoptr (i64 1 to %Result*))
  tail call void @__quantum__rt__result_record_output(%Result* null, i8* nonnull getelementptr inbounds ([7 x i8], [7 x i8]* @cstr.72303030303000, i64 0, i64 0))
  tail call void @__quantum__rt__result_record_output(%Result* nonnull inttoptr (i64 1 to %Result*), i8* nonnull getelementptr inbounds ([7 x i8], [7 x i8]* @cstr.72303030303100, i64 0, i64 0))
  ret void
}

declare void @__quantum__qis__h__body(%Qubit*) local_unnamed_addr

declare void @__quantum__qis__mz__body(%Qubit*, %Result*) local_unnamed_addr #1

declare void @__quantum__rt__result_record_output(%Result*, i8*) local_unnamed_addr

declare void @__quantum__qis__cnot__body(%Qubit*, %Qubit*) local_unnamed_addr

attributes #0 = { "entry_point" "output_labeling_schema"="schema_id" "output_names"="[[[0,[0,\22r00000\22]],[1,[1,\22r00001\22]]]]" "qir_profiles"="base_profile" "requiredQubits"="2" "requiredResults"="2" }
attributes #1 = { "irreversible" }

!llvm.module.flags = !{!0}

!0 = !{i32 2, !"Debug Info Version", i32 3}
